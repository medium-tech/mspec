import json
import os
import shutil
import subprocess
import time

from pathlib import Path
from typing import Callable, NamedTuple
from urllib.parse import unquote

from lingolib.context import (
    LingoContext,
    LingoRegisteredFunction,
)
from lingolib.errors import LingoRuntimeError
from lingolib.parsing import LingoASTAppSpec
from lingolib.types import LingoLanguageError

from lingolib.runtime.eval_expression import unwrap_expression
from lingolib.runtime.registry import add_lib_to_registry, init_registry
from lingolib.runtime.shared import (
    DEFAULT_HOST,
    DEFAULT_LOG_MAX_SIZE,
    DEFAULT_MAX_BODY_BYTES,
    DEFAULT_PORT,
    DEFAULT_SERVER_PROCESSES,
)


UWSGI_LOG_FORMAT = "%('    ') :: RESP :: %(status) :: %(method) %(uri) :: %(size) bytes in %(msecs) msecs :: %(request_id)"



class ServerConfig(NamedTuple):
    host: str
    port: int
    processes: int
    max_body_bytes: int
    log_max_size: int


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
    
    return ServerConfig(host, port, processes, max_body_bytes, log_max_size)


def _json_value(value):
    if isinstance(value, LingoLanguageError):
        return {'error': value.error, 'code': value.code}
    else:
        return value


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


def create_wsgi_application(
    ctx: LingoContext,
    ast: LingoASTAppSpec,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> Callable:
    init_registry(ctx)
    add_lib_to_registry(ctx, ast.imports)
    routes = {
        (module_name, op_name): op
        for module_name, module in ast.modules.members.items()
        for op_name, op in module.ops.funcs.items()
    }

    def application(env, start_response):
        method = env.get('REQUEST_METHOD', '')
        path = env.get('PATH_INFO', '')
        response_status = '200 OK'
        response_payload = None

        if method != 'POST':
            response_status = '405 Method Not Allowed'
            response_payload = {'error': 'only POST requests are supported'}
        else:
            parts = [unquote(part) for part in path.strip('/').split('/')]
            if len(parts) != 2 or not all(parts):
                response_status = '404 Not Found'
                response_payload = {'error': 'expected path /<module>/<op>'}
            else:
                func = routes.get((parts[0], parts[1]))
                if func is None:
                    response_status = '404 Not Found'
                    response_payload = {'error': f'op not found: {parts[0]}.{parts[1]}'}
                else:
                    try:
                        content_length = int(env.get('CONTENT_LENGTH') or '0')
                        if content_length < 0 or content_length > max_body_bytes:
                            raise ValueError('request body size is invalid or exceeds the limit')
                        body = env['wsgi.input'].read(content_length)
                        if len(body) != content_length:
                            raise ValueError('request body length does not match CONTENT_LENGTH')
                        args = json.loads(body.decode('utf-8') or '{}')
                        if not isinstance(args, dict) or any(
                            not isinstance(key, str) for key in args
                        ):
                            raise ValueError('request JSON must be an object with string keys')
                        result = _run_op(ctx, func, args)
                        response_payload = _json_value(result)
                    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
                        response_status = '400 Bad Request'
                        response_payload = {'error': str(e)}
                    except LingoRuntimeError as e:
                        response_status = '400 Bad Request'
                        response_payload = {'error': str(e)}
                    except Exception:
                        ctx.log.exception('uncaught error while executing app op')
                        response_status = '500 Internal Server Error'
                        response_payload = {'error': 'internal server error'}

        encoded = json.dumps(response_payload).encode('utf-8')
        start_response(response_status, [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Content-Length', str(len(encoded))),
        ])
        return [encoded]

    return application


def _load_application_from_env():
    spec_path = os.environ.get('LINGO_APP_SPEC_FILE')
    if not spec_path:
        raise RuntimeError('LINGO_APP_SPEC_FILE must be set to the app spec path')

    from lingolib.api import create_ast_from_file

    max_body_bytes = _server_config().max_body_bytes
    ctx = LingoContext()
    ast = create_ast_from_file(ctx, spec_path)
    if not isinstance(ast, LingoASTAppSpec):
        raise LingoRuntimeError(f'server requires an app spec, got {ast.lingo.spec!r}')
    return create_wsgi_application(ctx, ast, max_body_bytes=max_body_bytes)


_application = None


def application(env, start_response):
    global _application
    import uwsgi  # only importable inside a uWSGI process

    if _application is None:
        _application = _load_application_from_env()
    request_id = f'{time.time_ns()}-{os.getpid()}'
    uwsgi.set_logvar('request_id', request_id)
    return _application(env, start_response)


def run_server(spec_path: str) -> None:
    uwsgi = shutil.which('uwsgi')
    if uwsgi is None:
        raise LingoRuntimeError('uWSGI is required for the server command; install it and ensure uwsgi is on PATH')

    config = _server_config()
    runtime_dir = Path(__file__).resolve().parent
    source_dir = runtime_dir.parents[1]
    env = os.environ.copy()
    env['LINGO_APP_SPEC_FILE'] = str(Path(spec_path).resolve())
    python_path = env.get('PYTHONPATH')
    env['PYTHONPATH'] = str(source_dir) if not python_path else f'{source_dir}{os.pathsep}{python_path}'
    command = [
        uwsgi,
        '--http', f'{config.host}:{config.port}',
        '--wsgi-file', str(Path(__file__).resolve()),
        '--callable', 'application',
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