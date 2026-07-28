import sys

from itertools import takewhile

from lingolib.api import execute_file, debug_file
from lingolib.context import LingoContext
from lingolib.types import value_to_str, error_to_str

HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path>    load, parse, execute an exe spec and print result\n'
    '  debug <path>  load, parse, print the AST for a spec\n'
    '\n'
    'supported specs: exe\n'
)

class LingoCLIParseError(Exception):
    pass


def parse_cli(ctx: LingoContext):
    args = sys.argv[1:]
    
    # collect options, command and remaining args

    options = list(takewhile(lambda arg: arg.startswith('-'), args))
    num_options = len(options)
    
    try:
        command = args[num_options]
    except IndexError:
        raise LingoCLIParseError('no command specified')

    remaining_args = args[num_options + 1:]

    # options and help

    if '--help' in options or '-h' in options:
        print(HELP)
        sys.exit(0)
    
    if '-v' in options or '--verbose' in options:
        ctx.log.setLevel('DEBUG')
        for handler in ctx.log.handlers:
            handler.setLevel('DEBUG')

    # command
   
    if command == 'exe':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('exe command requires only a path argument')
    
        result = execute_file(ctx, remaining_args[0])
        result_type = type(result).__name__
        ctx.log.debug(f'exe return type: {result_type}')
        
        if result_type == 'str':
            print(result)
            
        elif result_type == 'LingoLanguageError':
            print(error_to_str(result))
            
        else:
            print(value_to_str(result))

    elif command == 'debug':
        if len(remaining_args) != 1:
            raise LingoCLIParseError('debug command requires only a path argument')
        try:
            debug_file(ctx, remaining_args[0])

        except Exception as e:
            ctx.log.error(f'error generating AST: {e}', exc_info=True)
            sys.exit(1)
    else:
        raise LingoCLIParseError(f'unknown command: {command}')

def main(ctx: LingoContext):
    try:
        parse_cli(ctx)
    except LingoCLIParseError as e:
        ctx.log.error(f'CLI parse error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    ctx = LingoContext()
    main(ctx)
