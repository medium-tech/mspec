import sys

from itertools import takewhile

from lingolib.api import (
    execute_client_file,
    debug_file,
    display_file,
    execute_file,
    serve_file,
)
from lingolib.context import LingoContext
from lingolib.errors import LingoLibError
from lingolib.types import value_to_str, error_to_str
from lingolib.runtime.eval_client import print_response
from lingolib.runtime.eval_server import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SERVER_PROCESSES, DEFAULT_MAX_BODY_BYTES, DEFAULT_LOG_MAX_SIZE

HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path> <params>          load, parse, execute an exe spec and print result\n'
    '  display <path> <params>      load, parse, display a text or GUI spec\n'
    '  debug <path>                 load, parse, print the AST for a spec\n'
    '  server <app spec path>       run an app spec HTTP server\n'
    '  client <path> --op <module.op> [--json <object> | --params name=value ...] [-i] [--show]\n'
    '                               -i prompts for missing args (secure args use getpass); --show reveals secure output\n'
    '\n'
    'server/client environment:\n'
    f'  LINGO_SERVER_HOST            bind address (default: {DEFAULT_HOST})\n'
    f'  LINGO_SERVER_PORT            bind port (default: {DEFAULT_PORT})\n'
    f'  LINGO_SERVER_PROCESSES       uWSGI worker processes (default: {DEFAULT_SERVER_PROCESSES})\n'
    f'  LINGO_SERVER_MAX_BODY_BYTES  request body limit (default: {DEFAULT_MAX_BODY_BYTES})\n'
    f'  LINGO_SERVER_LOG_MAX_SIZE    uWSGI log rotation size in bytes (default: {DEFAULT_LOG_MAX_SIZE})\n'
    '  LINGO_CLIENT_HOST            server base URL (default: derived from host/port)\n'
    '\n'
    'server requires the uwsgi executable on PATH. Supported specs: app, exe, text, gui\n'
)

class LingoCLIParseError(Exception):
    pass


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
        request_body = None
        params = None
        interactive = False
        show_secure = False
        index = 0
        while index < len_client_options:
            flag = client_options[index]
            if flag == '-i':
                if interactive:
                    raise LingoCLIParseError('-i may only be specified once')
                interactive = True
                index += 1
                continue
            if flag == '--show':
                if show_secure:
                    raise LingoCLIParseError('--show may only be specified once')
                show_secure = True
                index += 1
                continue
            if flag == '--params':
                if params is not None:
                    raise LingoCLIParseError('--params may only be specified once')
                params = []
                index += 1
                while index < len_client_options and not client_options[index].startswith('-'):
                    params.append(client_options[index])
                    index += 1
                continue
            if flag not in ('--op', '--json'):
                raise LingoCLIParseError(f'unknown client option: {flag}')
            if index + 1 >= len_client_options:
                raise LingoCLIParseError(f'{flag} requires a value')
            value = client_options[index + 1]
            if flag == '--op':
                if op_reference is not None:
                    raise LingoCLIParseError('--op may only be specified once')
                op_reference = value
            else:
                if request_body is not None:
                    raise LingoCLIParseError('--json may only be specified once')
                request_body = value
            index += 2
        if op_reference is None:
            raise LingoCLIParseError('client command requires --op <module.op>')
        if params == [] and not interactive:
            raise LingoCLIParseError('--params requires at least one name=value')
        if request_body is None:
            if params is None and not interactive:
                raise LingoCLIParseError(
                    'client command requires --json, --params, or -i'
                )
        elif params is not None or interactive:
            raise LingoCLIParseError('--json cannot be combined with --params or -i')

        response = execute_client_file(
            ctx,
            spec_path,
            op_reference,
            request_body=request_body,
            params=params,
            interactive=interactive,
            show_secure=show_secure,
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
