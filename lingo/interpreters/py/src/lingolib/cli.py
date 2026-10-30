import sys

from itertools import takewhile

from lingolib.api import (
    create_ast_from_file,
    execute_client_file,
    debug_file,
    display_file,
    execute_file,
    serve_file,
)
from lingolib.ast import LingoASTAppSpec
from lingolib.context import LingoContext
from lingolib.errors import LingoLibError
from lingolib.symbols import L_SYM_define
from lingolib.runtime.eval_expression import unwrap_expression
from lingolib.types import value_to_str, error_to_str
from lingolib.runtime.eval_client import ClientModelRequest, fetch_server_spec, print_response, resolve_client_model, resolve_client_op
from lingolib.runtime.shared import DEFAULT_DB_FILE, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SERVER_PROCESSES, DEFAULT_MAX_BODY_BYTES, DEFAULT_LOG_MAX_SIZE

HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path> <params>          load, parse, execute an exe spec and print result\n'
    '  display <path> <params>      load, parse, display a text or GUI spec\n'
    '  debug <path>                 load, parse, print the AST for a spec\n'
    '  server <app spec path>       run an app spec HTTP server\n'
    '  client <path> --op <module.op> [--json <object> | --params name=value ...] [-i] [--show]\n'
    '  client <path> --model <module.model> <action> [--json <object> | --params name=value ...] [-i] [--show]\n'
    '                               -i prompts for missing args (secure args use getpass); --show reveals secure output\n'
    '                               actions: --create, --list [--offset N] [--limit N], --get ID, --put ID, --patch ID, --delete ID\n'
    '                               create/put/patch must provide model field(s) with --json, --params or -i\n'
    '  client <path> --lingo spec   fetch the original yaml app spec from the server\n'
    '\n'
    'server/client environment:\n'
    f'  LINGO_SERVER_HOST            bind address (default: {DEFAULT_HOST})\n'
    f'  LINGO_SERVER_PORT            bind port (default: {DEFAULT_PORT})\n'
    f'  LINGO_SERVER_PROCESSES       uWSGI worker processes (default: {DEFAULT_SERVER_PROCESSES})\n'
    f'  LINGO_SERVER_MAX_BODY_BYTES  request body limit (default: {DEFAULT_MAX_BODY_BYTES})\n'
    f'  LINGO_SERVER_LOG_MAX_SIZE    uWSGI log rotation size in bytes (default: {DEFAULT_LOG_MAX_SIZE})\n'
    f'  LINGO_SERVER_DB_FILE         sqlite file for app models (default: {DEFAULT_DB_FILE})\n'
    '  LINGO_CLIENT_HOST            server base URL (default: derived from host/port)\n'
    '\n'
    'server requires the uwsgi executable on PATH. Supported specs: app, exe, text, gui\n'
)

class LingoCLIParseError(Exception):
    pass


def create_app_spec_help(ctx: LingoContext, spec_path: str) -> str:
    ast = create_ast_from_file(ctx, spec_path)
    if not isinstance(ast, LingoASTAppSpec):
        raise LingoCLIParseError(f'client requires an app spec, got {ast.lingo.spec!r}')

    meta = ast.meta.values if ast.meta else {}
    lines = [
        'app spec:',
        f'    title: {meta.get("title", "unknown")}',
        f'    description: {meta.get("description", "none")}',
        '',
        '    modules:',
    ]
    for module_name, module in ast.modules.members.items():
        lines.append(f'        {module_name}:')
        lines.append('            ops:')
        lines.extend(f'                {module_name}.{op_name}' for op_name in module.ops.funcs)
        lines.append('            models:')
        lines.extend(f'                {module_name}.{model_name}' for model_name in module.models)

    return '\n'.join(lines)


def _describe_define(ctx: LingoContext, define: L_SYM_define, indent: str) -> list[str]:
    type_str = define.type
    if define.element_type:
        type_str = f'{type_str}[{define.element_type}]'

    line = f'{indent}{define.name}: ({type_str})'
    if define.default is not None:
        line += f' default={unwrap_expression(ctx, define.default)!r}'
    if define.secure:
        line += ' secure'
    if define.description:
        line += f' :: {define.description}'

    lines = [line]
    for field in (define.fields or {}).values():
        lines.extend(_describe_define(ctx, field, indent + '    '))
    return lines


def create_model_help(ctx: LingoContext, spec_path: str, model_reference: str) -> str:
    ast = create_ast_from_file(ctx, spec_path)
    if not isinstance(ast, LingoASTAppSpec):
        raise LingoCLIParseError(f'client requires an app spec, got {ast.lingo.spec!r}')

    define = resolve_client_model(ctx, ast, model_reference)
    lines = [
        'model:',
        f'    name: {model_reference}',
        f'    description: {define.description or "none"}',
        '',
        '    fields:',
    ]
    for field in (define.fields or {}).values():
        lines.extend(_describe_define(ctx, field, '        '))
    return '\n'.join(lines)


def create_op_help(ctx: LingoContext, spec_path: str, op_reference: str) -> str:
    ast = create_ast_from_file(ctx, spec_path)
    if not isinstance(ast, LingoASTAppSpec):
        raise LingoCLIParseError(f'client requires an app spec, got {ast.lingo.spec!r}')

    op = resolve_client_op(ctx, ast, op_reference)
    lines = [
        'op:',
        f'    name: {op_reference}',
        f'    description: {op.description or "none"}',
        '',
        '    params:',
    ]
    for arg in op.args or []:
        lines.extend(_describe_define(ctx, arg, '        '))
    lines.extend(['', '    return:'])
    if op.return_ is None:
        lines.append('        none')
    else:
        return_lines = _describe_define(ctx, op.return_, '        ')
        # the return define's generated name (<op>.return) is noise
        return_lines[0] = return_lines[0].replace(f'{op.return_.name} ', '', 1)
        lines.extend(return_lines)
    return '\n'.join(lines)


def _client_help_target(remaining_args: list[str]) -> tuple[str, str] | None:
    """return ('op' | 'model', reference) if --op or --model is given a value in the client args"""
    for flag in ('--op', '--model'):
        if flag in remaining_args:
            index = remaining_args.index(flag)
            if index + 1 >= len(remaining_args) or remaining_args[index + 1].startswith('-'):
                raise LingoCLIParseError(f'{flag} requires a value')
            return flag[2:], remaining_args[index + 1]
    return None


def parse_cli(ctx: LingoContext):

    args = sys.argv[1:]

    # options and help #

    options = list(takewhile(lambda arg: arg.startswith('-'), args))

    if '--help' in options or '-h' in options:
        print(HELP)
        sys.exit(0)
    
    if '-v' in options or '--verbose' in options:
        ctx.log.setLevel('DEBUG')
        for handler in ctx.log.handlers:
            handler.setLevel('DEBUG')

    # command #

    num_options = len(options)
    
    try:
        command = args[num_options]
    except IndexError:
        raise LingoCLIParseError('no command specified')

    remaining_args = args[num_options + 1:]

    if '--help' in remaining_args or '-h' in remaining_args:
        print(HELP)
        if command == 'client' and remaining_args and not remaining_args[0].startswith('-'):
            spec_path = remaining_args[0]
            target = _client_help_target(remaining_args)
            match target:
                case ('op', reference):
                    print(create_op_help(ctx, spec_path, reference))
                case ('model', reference):
                    print(create_model_help(ctx, spec_path, reference))
                case _:
                    print(create_app_spec_help(ctx, spec_path))
        return

    if command == 'exe':
        if len(remaining_args) < 1:
            raise LingoCLIParseError('exe command requires a path argument')
    
        result = execute_file(ctx, remaining_args[0], cli_args=remaining_args[1:])
        result_type = type(result).__name__
        ctx.log.debug(f'exe return type: {result_type}')
        
        if result_type == 'str':
            print(result)
            
        elif result_type == 'LingoLanguageError':
            print(error_to_str(result))
            
        else:
            print(value_to_str(result))

    elif command == 'display':
        if len(remaining_args) < 1:
            raise LingoCLIParseError('display command requires a path argument')
        
        try:
            display_file(ctx, remaining_args[0], cli_args=remaining_args[1:])

        except Exception as e:
            ctx.log.error(f'error displaying spec: {e}', exc_info=True)
            sys.exit(1)

    elif command == 'debug':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('debug command requires only a path argument')
        try:
            debug_file(ctx, remaining_args[0])

        except Exception as e:
            ctx.log.error(f'error generating AST: {e}', exc_info=True)
            sys.exit(1)
    elif command == 'server':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('server command requires only an app spec path')
        serve_file(ctx, remaining_args[0])

    elif command == 'client':
        try:
            spec_path = remaining_args[0]
        except IndexError:
            raise LingoCLIParseError('client command requires an app spec path')
        
        client_options = remaining_args[1:]
        len_client_options = len(client_options)
        op_reference = None
        model = None
        action = None
        item_id = None
        offset = None
        limit = None
        request_body = None
        params = None
        interactive = False
        show_secure = False
        index = 0
        while index < len_client_options:
            flag = client_options[index]
            match flag:
                case '-i':
                    if interactive:
                        raise LingoCLIParseError('-i may only be specified once')
                    interactive = True
                    index += 1

                case '--show':
                    if show_secure:
                        raise LingoCLIParseError('--show may only be specified once')
                    show_secure = True
                    index += 1

                case '--params':
                    if params is not None:
                        raise LingoCLIParseError('--params may only be specified once')
                    params = []
                    index += 1
                    while index < len_client_options and not client_options[index].startswith('-'):
                        params.append(client_options[index])
                        index += 1

                case '--create' | '--list':
                    if action is not None:
                        raise LingoCLIParseError('only one model action may be specified')
                    action = flag[2:]
                    index += 1

                case '--lingo':
                    if index + 1 >= len_client_options:
                        raise LingoCLIParseError('--lingo requires a value')
                    if client_options[index + 1] != 'spec':
                        raise LingoCLIParseError(f'--lingo only supports: spec, got {client_options[index + 1]!r}')
                    if len_client_options != 2:
                        raise LingoCLIParseError('--lingo cannot be combined with other client options')
                    print(fetch_server_spec(), end='')
                    return

                case '--op' | '--model' | '--json'  | '--offset' | '--limit' | '--get' | '--put' | '--patch' | '--delete':
                    if index + 1 >= len_client_options:
                        raise LingoCLIParseError(f'{flag} requires a value')
                    value = client_options[index + 1]
                    index += 2
                    match flag:
                        case '--op':
                            if op_reference is not None:
                                raise LingoCLIParseError('--op may only be specified once')
                            op_reference = value
                        case '--model':
                            if model is not None:
                                raise LingoCLIParseError('--model may only be specified once')
                            model = value
                        case '--json':
                            if request_body is not None:
                                raise LingoCLIParseError('--json may only be specified once')
                            request_body = value
                        case '--offset':
                            if offset is not None:
                                raise LingoCLIParseError(f'--offset may only be specified once')
                            try:
                                offset = int(value)
                            except ValueError:
                                raise LingoCLIParseError(f'--offset must be an int, got {value!r}') from None
                            
                        case '--limit':
                            if limit is not None:
                                raise LingoCLIParseError(f'--limit may only be specified once')
                            try:
                                limit = int(value)
                            except ValueError:
                                raise LingoCLIParseError(f'--limit must be an int, got {value!r}') from None
                            
                        case _:	# matches --get, --put, --patch, --delete
                            if action is not None:
                                raise LingoCLIParseError('only one model action may be specified')
                            action = flag[2:]
                            item_id = value

                case _:
                    raise LingoCLIParseError(f'unknown client option: {flag}')

        if op_reference is not None and model is not None:
            raise LingoCLIParseError('--op and --model cannot be combined')

        model_request = None
        if op_reference is None:
            if model is None:
                raise LingoCLIParseError('client command requires --op <module.op> or --model <module.model>')
            if action is None:
                raise LingoCLIParseError('--model requires an action: --create, --list, --get, --put, --patch or --delete')
            model_request = ClientModelRequest(model, action, item_id=item_id, offset=offset, limit=limit)
            needs_body = action in ('create', 'put')
            allows_body = needs_body or action == 'patch'
        else:
            if action is not None or offset is not None or limit is not None:
                raise LingoCLIParseError('model actions, --offset and --limit require --model')
            needs_body = allows_body = True

        if (offset is not None or limit is not None) and action != 'list':
            raise LingoCLIParseError('--offset and --limit require --list')

        has_body_args = request_body is not None or params is not None or interactive
        if not allows_body:
            if has_body_args:
                raise LingoCLIParseError(f'--{action} does not accept --json, --params or -i')
        else:
            if params == [] and not interactive:
                raise LingoCLIParseError('--params requires at least one name=value')

            if request_body is None:
                if needs_body and params is None and not interactive:
                    raise LingoCLIParseError('client command requires --json, --params, or -i')
                if action == 'patch' and params is None:
                    raise LingoCLIParseError('--patch requires --json or --params')
            elif params is not None or interactive:
                raise LingoCLIParseError('--json cannot be combined with --params or -i')

            if action == 'patch' and interactive:
                raise LingoCLIParseError('-i cannot be used with --patch')

        response = execute_client_file(
            ctx,
            spec_path,
            op_reference,
            request_body=request_body,
            params=params,
            interactive=interactive,
            show_secure=show_secure,
            model_request=model_request,
        )
        print_response(response)
        
    else:
        raise LingoCLIParseError(f'unknown command: {command}')

def main(ctx: LingoContext):
    try:
        parse_cli(ctx)
    except LingoCLIParseError as e:
        ctx.log.error(f'CLI parse error: {e}')
        sys.exit(1)
    except LingoLibError as e:
        ctx.log.error(f'lingo error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    ctx = LingoContext()
    main(ctx)
