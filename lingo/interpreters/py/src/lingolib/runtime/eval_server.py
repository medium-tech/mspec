import json
import os
import re
import shutil
import sqlite3
import subprocess
import time

from contextlib import closing
from http import HTTPStatus
from pathlib import Path
from typing import Callable, NamedTuple
from urllib.parse import parse_qs, unquote

from lingolib.context import (
    LingoContext,
    LingoDBRuntimeContext,
    LingoRegisteredFunction,
)
from lingolib.errors import LingoRuntimeError
from lingolib.parsing import LingoASTAppSpec, create_ast_from_file
from lingolib.symbols import L_SYM_define
from lingolib.types import LingoLanguageError, LingoValue

from lingolib.runtime.eval_expression import (
    LingoErrorPassThrough,
    _validate_value_against_define,
    raise_error,
    register_expression_handlers,
    unwrap_expression,
)
from lingolib.runtime.registry import add_lib_to_registry, init_registry, resolve_model_define
from lingolib.runtime.shared import (
    DEFAULT_DB_FILE,
    DEFAULT_HOST,
    DEFAULT_LIST_LIMIT,
    DEFAULT_LOG_MAX_SIZE,
    DEFAULT_MAX_BODY_BYTES,
    DEFAULT_PORT,
    DEFAULT_SERVER_PROCESSES,
    MAX_LIST_LIMIT,
)


UWSGI_LOG_FORMAT = "%('    ') :: RESP :: %(status) :: %(method) %(uri) :: %(size) bytes in %(msecs) msecs :: %(request_id)"

#
# config
#

class ServerConfig(NamedTuple):
    host: str
    port: int
    processes: int
    max_body_bytes: int
    log_max_size: int
    db_file: str


def _server_config() -> ServerConfig:
    host = os.environ.get('LINGO_SERVER_HOST', DEFAULT_HOST).strip()

    if not host:
        raise LingoRuntimeError(f'LINGO_SERVER_HOST must not be empty string')
    
    try:
        port = int(os.environ.get('LINGO_SERVER_PORT', DEFAULT_PORT))
    except ValueError:
        raise LingoRuntimeError(f'invalid LINGO_SERVER_PORT env value, must be int') from None

    if not 0 < port < 65536:
        raise LingoRuntimeError(f'LINGO_SERVER_PORT must be between 1 and 65535, got {port}')

    try:
        processes = int(os.environ.get('LINGO_SERVER_PROCESSES', DEFAULT_SERVER_PROCESSES))
    except ValueError:
        raise LingoRuntimeError(f'invalid LINGO_SERVER_PROCESSES env value, must be int') from None

    if processes < 1:
        raise LingoRuntimeError(f'LINGO_SERVER_PROCESSES must be at least 1, got {processes}')

    try:
        max_body_bytes = int(os.environ.get('LINGO_SERVER_MAX_BODY_BYTES', DEFAULT_MAX_BODY_BYTES))
    except ValueError:
        raise LingoRuntimeError(f'invalid LINGO_SERVER_MAX_BODY_BYTES env value, must be int') from None
    
    if max_body_bytes < 1:
        raise LingoRuntimeError(f'LINGO_SERVER_MAX_BODY_BYTES must be at least 1, got {max_body_bytes}')

    try:
        log_max_size = int(os.environ.get('LINGO_SERVER_LOG_MAX_SIZE', DEFAULT_LOG_MAX_SIZE))
    except ValueError:
        raise LingoRuntimeError(f'invalid LINGO_SERVER_LOG_MAX_SIZE env value, must be int') from None

    if log_max_size < 1:
        raise LingoRuntimeError(f'LINGO_SERVER_LOG_MAX_SIZE must be at least 1, got {log_max_size}')
    
    db_file = os.environ.get('LINGO_SERVER_DB_FILE', DEFAULT_DB_FILE).strip()

    if not db_file:
        raise LingoRuntimeError('LINGO_SERVER_DB_FILE must not be empty string')

    return ServerConfig(host, port, processes, max_body_bytes, log_max_size, db_file)


#
# db helpers
#

SQL_TYPES = {'str': 'TEXT', 'int': 'INTEGER', 'float': 'REAL', 'bool': 'INTEGER'}
IDENTIFIER_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

# error codes mapped to http status, any other LingoLanguageError code is a 500
ERROR_CODE_STATUS = {
    'DB_NOT_FOUND': HTTPStatus.NOT_FOUND,
    'VALIDATION_ERROR': HTTPStatus.BAD_REQUEST,
}

# context #

def init_db(ctx: LingoContext, ast: LingoASTAppSpec, db_file: str):
    """resolve the app's models, check they are supported and create their tables"""
    ctx.db = LingoDBRuntimeContext(path=db_file)

    table_names = {}
    for module_name, module in ast.modules.members.items():
        for model_name, model in module.models.items():
            model_key = f'{module_name}.{model_name}'

            if model_name in module.ops.funcs:
                raise LingoRuntimeError(f'module {module_name!r} defines both an op and a model named {model_name!r}')
            if not IDENTIFIER_PATTERN.match(module_name) or not IDENTIFIER_PATTERN.match(model_name):
                raise LingoRuntimeError(f'model {model_key!r} cannot be used as a database table name')

            table = _table_name(model_key)
            if table in table_names:
                raise LingoRuntimeError(f'models {table_names[table]!r} and {model_key!r} map to the same table {table!r}')
            table_names[table] = model_key

            define = resolve_model_define(ctx, model)
            _check_model(model_key, define)
            ctx.db.models[model_key] = define
            if model.reference is not None:
                ctx.db.references.setdefault(model.reference, []).append(model_key)

    with closing(sqlite3.connect(db_file)) as conn:
        for model_key, define in ctx.db.models.items():
            _create_table(conn, model_key, define)
        conn.commit()

# model #

def _resolve_db_model(ctx: LingoContext, model_ref: str) -> tuple[str, L_SYM_define] | LingoLanguageError:
    """model_ref is either an app model, <module>.<model>, or the lib reference that an app model points to"""
    if ctx.db is None:
        return LingoLanguageError('no database is available in this runtime', code='DB_NOT_CONFIGURED')

    if model_ref in ctx.db.models:
        return model_ref, ctx.db.models[model_ref]

    model_keys = ctx.db.references.get(model_ref, [])
    if len(model_keys) == 1:
        return model_keys[0], ctx.db.models[model_keys[0]]
    if len(model_keys) > 1:
        return LingoLanguageError(f'model reference {model_ref!r} is used by multiple app models: {", ".join(model_keys)}', code='DB_MODEL_AMBIGUOUS')

    return LingoLanguageError(f'model {model_ref!r} is not defined by the app spec', code='DB_MODEL_NOT_FOUND')

def _check_model(model_key: str, define: L_SYM_define):
    if define.type != 'struct' or not define.fields:
        raise LingoRuntimeError(f'model {model_key!r} must be a struct with at least one field')

    for field_name, field_define in define.fields.items():
        if not IDENTIFIER_PATTERN.match(field_name):
            raise LingoRuntimeError(f'field name {field_name!r} of model {model_key!r} is not a valid database column name')
        if field_name == 'id':
            raise LingoRuntimeError(f'model {model_key!r} cannot define a field named "id", it is reserved for the generated id')
        if field_define.type not in SQL_TYPES:
            raise LingoRuntimeError(
                f'field {field_name!r} of model {model_key!r} has type {field_define.type!r}, only scalar types are supported: {", ".join(SQL_TYPES)}'
            )

def _apply_defaults(ctx: LingoContext, define: L_SYM_define, data):
    if not isinstance(data, dict):
        return data

    with_defaults = dict(data)
    for name, field in define.fields.items():
        if name not in with_defaults and field.default is not None:
            with_defaults[name] = unwrap_expression(ctx, field.default)
    return with_defaults

def _table_name(model_key: str) -> str:
    return model_key.replace('.', '_')

# table ops #

def _create_table(conn: sqlite3.Connection, model_key: str, define: L_SYM_define):
    table = _table_name(model_key)
    columns = ''.join(f', "{name}" {SQL_TYPES[field.type]}' for name, field in define.fields.items())
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" (id INTEGER PRIMARY KEY AUTOINCREMENT{columns})')

    table_info = list(conn.execute(f'PRAGMA table_info("{table}")'))
    existing = [row[1] for row in table_info]
    expected = ['id', *define.fields]
    if existing != expected:
        raise LingoRuntimeError(f'existing table {table!r} has columns {existing}, expected {expected}')
    if table_info[0][2].upper() != 'INTEGER' or table_info[0][5] != 1:
        raise LingoRuntimeError(
            f'existing table {table!r} must use INTEGER PRIMARY KEY AUTOINCREMENT for id'
        )
    create_sql = conn.execute(
        'SELECT sql FROM sqlite_master WHERE type = ? AND name = ?',
        ('table', table),
    ).fetchone()[0]
    if 'AUTOINCREMENT' not in create_sql.upper():
        raise LingoRuntimeError(
            f'existing table {table!r} must use INTEGER PRIMARY KEY AUTOINCREMENT for id'
        )

def _select_row(conn: sqlite3.Connection, model_key: str, define: L_SYM_define, item_id) -> tuple | None:
    columns = ', '.join(['id', *(f'"{name}"' for name in define.fields)])
    return conn.execute(
        f'SELECT {columns} FROM "{_table_name(model_key)}" WHERE id = ?',
        (_to_db_id(item_id),),
    ).fetchone()

def _read_list_query(env) -> dict:
    query = parse_qs(env.get('QUERY_STRING', ''), keep_blank_values=True)
    unknown = set(query) - {'offset', 'limit'}
    if unknown:
        raise ValueError(f'unsupported query parameter(s): {", ".join(sorted(unknown))}')

    options = {}
    for name, values in query.items():
        if len(values) != 1:
            raise ValueError(f'query parameter {name!r} may only be specified once')
        try:
            options[name] = int(values[0])
        except ValueError:
            raise ValueError(f'query parameter {name!r} must be an int, got {values[0]!r}') from None
    return options

# conversion #

def _row_to_object(define: L_SYM_define, row: tuple) -> dict:
    obj = {'id': str(row[0])}
    for (name, field), value in zip(define.fields.items(), row[1:]):
        obj[name] = bool(value) if field.type == 'bool' else value
    return obj

def _to_sql(value):
    return int(value) if isinstance(value, bool) else value

def _to_db_id(item_id: str) -> int | None:
    try:
        return int(item_id)
    except ValueError:
        return None

# errors #

def _check_id(item_id) -> LingoLanguageError | None:
    if not isinstance(item_id, str) or not item_id:
        return LingoLanguageError(f'id must be a non-empty str, got {item_id!r}', code='VALIDATION_ERROR')
    return None

def _not_found(model_key: str, item_id) -> LingoLanguageError:
    return LingoLanguageError(f'{model_key} with id {item_id!r} not found', code='DB_NOT_FOUND')

#
# db symbol evaluators
#

# crud + list #

def _eval_db_create(ctx: LingoContext, model_ref: str, data) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    data = _apply_defaults(ctx, define, data)
    validation_error = _validate_value_against_define(data, define)
    if validation_error is not None:
        return validation_error

    names = list(define.fields)
    columns = ', '.join(f'"{name}"' for name in names)
    placeholders = ', '.join('?' * len(names))
    with closing(sqlite3.connect(ctx.db.path)) as conn:
        cursor = conn.execute(
            f'INSERT INTO "{_table_name(model_key)}" ({columns}) VALUES ({placeholders})',
            [_to_sql(data[name]) for name in names],
        )
        item_id = str(cursor.lastrowid)
        conn.commit()

    return {'id': item_id, **{name: data[name] for name in names}}

def _eval_db_read(ctx: LingoContext, model_ref: str, item_id) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    id_error = _check_id(item_id)
    if id_error is not None:
        return id_error

    with closing(sqlite3.connect(ctx.db.path)) as conn:
        row = _select_row(conn, model_key, define, item_id)

    if row is None:
        return _not_found(model_key, item_id)
    return _row_to_object(define, row)

def _eval_db_list(ctx: LingoContext, model_ref: str, offset=None, limit=None) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    offset = 0 if offset is None else offset
    limit = DEFAULT_LIST_LIMIT if limit is None else limit
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        return LingoLanguageError(f'offset must be an int >= 0, got {offset!r}', code='VALIDATION_ERROR')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIST_LIMIT:
        return LingoLanguageError(f'limit must be an int between 1 and {MAX_LIST_LIMIT}, got {limit!r}', code='VALIDATION_ERROR')

    table = _table_name(model_key)
    columns = ', '.join(['id', *(f'"{name}"' for name in define.fields)])
    with closing(sqlite3.connect(ctx.db.path)) as conn:
        total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        rows = conn.execute(
            f'SELECT {columns} FROM "{table}" ORDER BY rowid LIMIT ? OFFSET ?', (limit, offset)
        ).fetchall()

    return {'items': [_row_to_object(define, row) for row in rows], 'total': total}

def _eval_db_put(ctx: LingoContext, model_ref: str, item_id, data) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    id_error = _check_id(item_id)
    if id_error is not None:
        return id_error

    data = _apply_defaults(ctx, define, data)
    validation_error = _validate_value_against_define(data, define)
    if validation_error is not None:
        return validation_error

    names = list(define.fields)
    assignments = ', '.join(f'"{name}" = ?' for name in names)
    with closing(sqlite3.connect(ctx.db.path)) as conn:
        cursor = conn.execute(
            f'UPDATE "{_table_name(model_key)}" SET {assignments} WHERE id = ?',
            [*(_to_sql(data[name]) for name in names), _to_db_id(item_id)],
        )
        conn.commit()

    if cursor.rowcount == 0:
        return _not_found(model_key, item_id)
    return {'id': item_id, **{name: data[name] for name in names}}

def _eval_db_patch(ctx: LingoContext, model_ref: str, item_id, data) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    id_error = _check_id(item_id)
    if id_error is not None:
        return id_error

    validation_error = _validate_value_against_define(data, define, partial=True)
    if validation_error is not None:
        return validation_error
    if not data:
        return LingoLanguageError('patch requires at least one field', code='VALIDATION_ERROR')

    names = [name for name in define.fields if name in data]
    assignments = ', '.join(f'"{name}" = ?' for name in names)
    with closing(sqlite3.connect(ctx.db.path)) as conn:
        cursor = conn.execute(
            f'UPDATE "{_table_name(model_key)}" SET {assignments} WHERE id = ?',
            [*(_to_sql(data[name]) for name in names), _to_db_id(item_id)],
        )
        conn.commit()
        if cursor.rowcount == 0:
            return _not_found(model_key, item_id)
        row = _select_row(conn, model_key, define, item_id)

    return _row_to_object(define, row)

def _eval_db_delete(ctx: LingoContext, model_ref: str, item_id) -> dict | LingoLanguageError:
    resolved = _resolve_db_model(ctx, model_ref)
    if isinstance(resolved, LingoLanguageError):
        return resolved
    model_key, define = resolved

    id_error = _check_id(item_id)
    if id_error is not None:
        return id_error

    with closing(sqlite3.connect(ctx.db.path)) as conn:
        row = _select_row(conn, model_key, define, item_id)
        if row is None:
            return _not_found(model_key, item_id)
        conn.execute(
            f'DELETE FROM "{_table_name(model_key)}" WHERE id = ?',
            (_to_db_id(item_id),),
        )
        conn.commit()

    return _row_to_object(define, row)

# handler + registration #

def _eval_db_symbol(ctx: LingoContext, db_func: Callable, symbol, *arg_names: str):
    try:
        args = [
            None if getattr(symbol, name) is None else raise_error(unwrap_expression(ctx, getattr(symbol, name)))
            for name in arg_names
        ]
    except LingoErrorPassThrough as e:
        return e.error

    result = db_func(ctx, symbol.model, *args)
    if isinstance(result, LingoLanguageError):
        return result
    return LingoValue(type='struct', value=result)

register_expression_handlers({
    'db_create': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_create, symbol, 'data'),
    'db_read': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_read, symbol, 'id'),
    'db_list': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_list, symbol, 'offset', 'limit'),
    'db_put': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_put, symbol, 'id', 'data'),
    'db_patch': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_patch, symbol, 'id', 'data'),
    'db_delete': lambda ctx, symbol: _eval_db_symbol(ctx, _eval_db_delete, symbol, 'id'),
})

#
# wsgi helpers
#

def _run_op(ctx: LingoContext, func, args: dict):
    if func.reference is not None:
        try:
            registered = ctx.registry.lib[func.reference]
        except KeyError:
            raise LingoRuntimeError(f'op reference {func.reference!r} not found') from None
        if not isinstance(registered, LingoRegisteredFunction):
            raise LingoRuntimeError(f'op reference {func.reference!r} is not a function')
        func = registered.ast

    if func.func is None or func.args is None:
        raise LingoRuntimeError(f'op {func.name!r} if missing func body or args')

    arg_definitions = {arg.name: arg for arg in func.args}
    unknown_args = set(args) - set(arg_definitions)
    if unknown_args:
        raise LingoRuntimeError(f'unknown argument(s) for op {func.name}: {", ".join(unknown_args)}')

    for arg_name, definition in arg_definitions.items():
        if arg_name not in args:
            if definition.default is None:
                raise LingoRuntimeError(f'missing required argument: {arg_name}')
            args[arg_name] = unwrap_expression(ctx, definition.default)

    ctx.registry.call_args_stack.append(args)
    try:
        return unwrap_expression(ctx, func.func)
    finally:
        ctx.registry.call_args_stack.pop()

# json #

def _read_json_body(env, max_body_bytes: int) -> dict:
    content_length = int(env.get('CONTENT_LENGTH') or '0')
    if content_length < 0 or content_length > max_body_bytes:
        raise ValueError('request body size is invalid or exceeds the limit')
    body = env['wsgi.input'].read(content_length)
    if len(body) != content_length:
        raise ValueError('request body length does not match CONTENT_LENGTH')
    data = json.loads(body.decode('utf-8') or '{}')
    if not isinstance(data, dict):
        raise ValueError('request JSON must be an object')
    return data

def _json_value(value):
    if isinstance(value, LingoLanguageError):
        return {'error': value.error, 'code': value.code}
    else:
        return value

# response helpers #

def _response(status: HTTPStatus, payload, headers: list | None = None) -> tuple[str, object, list]:
    return f'{status.value} {status.phrase}', payload, headers or []

def _error_response(error: LingoLanguageError) -> tuple[str, object, list]:
    return _response(ERROR_CODE_STATUS.get(error.code, HTTPStatus.INTERNAL_SERVER_ERROR), _json_value(error))

def _result_response(result, success_status: HTTPStatus = HTTPStatus.OK) -> tuple[str, object, list]:
    if isinstance(result, LingoLanguageError):
        return _error_response(result)
    else:
        return _response(success_status, result)

#
# wsgi application
#

def create_wsgi_application(
    ctx: LingoContext,
    ast: LingoASTAppSpec,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    db_file: str = DEFAULT_DB_FILE,
) -> Callable:
    init_registry(ctx)
    add_lib_to_registry(ctx, ast.imports)
    init_db(ctx, ast, db_file)

    op_routes = {
        (module_name, op_name): op
        for module_name, module in ast.modules.members.items()
        for op_name, op in module.ops.funcs.items()
    }
    collection_methods = ('GET', 'POST')
    item_methods = ('GET', 'PUT', 'PATCH', 'DELETE')

    def handle_model(method: str, model_key: str, item_id: str | None, env):
        allowed = collection_methods if item_id is None else item_methods
        if method not in allowed:
            return _response(
                HTTPStatus.METHOD_NOT_ALLOWED,
                {'error': f'{method} is not supported for {model_key}, use: {", ".join(allowed)}'},
                [('Allow', ', '.join(allowed))],
            )

        match method, item_id:
            case 'GET', None:
                return _result_response(_eval_db_list(ctx, model_key, **_read_list_query(env)))
            case 'GET', _:
                return _result_response(_eval_db_read(ctx, model_key, item_id))
            case 'DELETE', _:
                return _result_response(_eval_db_delete(ctx, model_key, item_id))
            case 'POST', None:
                return _result_response(_eval_db_create(ctx, model_key, _read_json_body(env, max_body_bytes)), HTTPStatus.CREATED)
            case 'PUT', _:
                return _result_response(_eval_db_put(ctx, model_key, item_id, _read_json_body(env, max_body_bytes)))
            case 'PATCH', _:
                return _result_response(_eval_db_patch(ctx, model_key, item_id, _read_json_body(env, max_body_bytes)))
            case _:
                ctx.log.error(f'Unknown error, code should not get here, likely a bug, {method=} {model_key=} {item_id=}')
                raise LingoRuntimeError(f'Unknown error')

    def handle_op(method: str, func, env):
        if method != 'POST':
            return _response(
                HTTPStatus.METHOD_NOT_ALLOWED,
                {'error': f'ops only support POST, got {method}'},
                [('Allow', 'POST')],
            )
        return _result_response(_run_op(ctx, func, _read_json_body(env, max_body_bytes)))

    def route(env):
        method = env.get('REQUEST_METHOD', '')
        parts = [unquote(part) for part in env.get('PATH_INFO', '').strip('/').split('/')]
        if len(parts) not in (2, 3) or not all(parts):
            return _response(HTTPStatus.NOT_FOUND, {'error': 'expected path /<module>/<op> or /<module>/<model>[/<id>]'})

        module_name, name = parts[:2]
        item_id = parts[2] if len(parts) == 3 else None
        model_key = f'{module_name}.{name}'

        if item_id is None and (module_name, name) in op_routes:
            return handle_op(method, op_routes[(module_name, name)], env)
        elif model_key in ctx.db.models:
            return handle_model(method, model_key, item_id, env)
        else:
            return _response(HTTPStatus.NOT_FOUND, {'error': f'not found: {"/".join(parts)}'})

    def application(env, start_response):
        try:
            status, payload, headers = route(env)
        except (UnicodeDecodeError, ValueError, LingoRuntimeError) as e:
            status, payload, headers = _response(HTTPStatus.BAD_REQUEST, {'error': str(e)})
        except Exception:
            ctx.log.exception('uncaught error while handling request')
            status, payload, headers = _response(HTTPStatus.INTERNAL_SERVER_ERROR, {'error': 'internal server error'})

        encoded = json.dumps(payload).encode('utf-8')
        start_response(status, [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', str(len(encoded))),
            *headers,
        ])
        return [encoded]

    return application

def _create_uwsgi_application(spec_path: str) -> Callable:
    """used to import uWSGI application inside uWSGI subprocess only, for direct use use `create_wsgi_application`"""
    import uwsgi

    config = _server_config()
    ctx = LingoContext()
    ast = create_ast_from_file(ctx, spec_path)  # need to parse spec again because uWSGI is run in a separate process
                                                # and it's entrypoint is this file, not api.py or cli.py
    if not isinstance(ast, LingoASTAppSpec):
        raise LingoRuntimeError(f'server requires an app spec, got {ast.lingo.spec!r}')
    
    wsgi_application = create_wsgi_application(
        ctx, ast, max_body_bytes=config.max_body_bytes, db_file=config.db_file
    )

    def uwsgi_application(env, start_response):
        uwsgi.set_logvar('request_id', f'{time.time_ns()}-{os.getpid()}')
        return wsgi_application(env, start_response)

    return uwsgi_application

#
# entries
#

# from spec file #

def evaluate_server_spec(ctx: LingoContext, ast: LingoASTAppSpec) -> None:
    uwsgi = shutil.which('uwsgi')
    if uwsgi is None:
        raise LingoRuntimeError('uWSGI is required for the server command; install it and ensure uwsgi is on PATH')

    config = _server_config()

    # build the app once up front so spec/model/db errors surface here instead of in the uWSGI logs
    create_wsgi_application(ctx, ast, max_body_bytes=config.max_body_bytes, db_file=config.db_file)

    spec_path = str(Path(ast.lingo.L_FILE).resolve())
    runtime_dir = Path(__file__).resolve().parent
    source_dir = runtime_dir.parents[1]
    env = os.environ.copy()
    env['LINGO_APP_SPEC_FILE'] = spec_path
    python_path = env.get('PYTHONPATH')
    env['PYTHONPATH'] = str(source_dir) if not python_path else f'{source_dir}{os.pathsep}{python_path}'
    command = [
        uwsgi,
        '--http', f'{config.host}:{config.port}',
        # import by module name, loading this file by path would import it twice
        '--module', f'{__name__}:application',
        '--master',
        '--processes', str(config.processes),
        '--log-master',
        '--logformat', UWSGI_LOG_FORMAT,
        '--log-maxsize', str(config.log_max_size),
    ]
    try:
        subprocess.run(command, env=env, check=True)
    except FileNotFoundError:
        raise LingoRuntimeError(f'uWSGI executable not found: {uwsgi!r}') from None
    except subprocess.CalledProcessError as e:
        raise LingoRuntimeError(f'uWSGI exited with status {e.returncode}') from None

# actual server subprocess #

if os.environ.get('LINGO_APP_SPEC_FILE'):
    # The LINGO_APP_SPEC_FILE env var exists to tell this file whether or not to create the uwsgi application
	# when starting the server, api.py first imports this file but we don't want to create the uwsgi app yet
	# the evaluate_server_spec function will run the server as a subprocess, when it does that it will pass
	# the LINGO_APP_SPEC_FILE env var to tell this module to create the uwsgi application when needed
	# this env variable should NOT be set manually by users
    application = _create_uwsgi_application(os.environ['LINGO_APP_SPEC_FILE'])
