import sys
from pprint import pprint

from lingolib.api import execute_file, ast_from_file
from lingolib.context import LingoContext
from lingolib.parsing import print_lingo_ast
HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path>    load, parse, execute an exe spec and print result\n'
    '  ast <path>    load, parse, print the AST for a spec\n'
    '\n'
    'supported specs: exe\n'
)


def main(ctx: LingoContext):
    args = sys.argv[1:]
    if not args or args[0] in ('--help', '-h'):
        print(HELP, end='')
        return
    command = args[0]
    if command == 'exe':
        if len(args) < 2:
            print('error: exe requires a path argument', file=sys.stderr)
            sys.exit(1)
        try:
            result = execute_file(args[1])
            print(result)
        except Exception as e:
            print(f'error: {e}', file=sys.stderr)
            sys.exit(1)
    elif command == 'ast':
        if len(args) < 2:
            print('error: ast requires a path argument', file=sys.stderr)
            sys.exit(1)
        try:
            ast = ast_from_file(ctx, args[1])
            print_lingo_ast(ast)

        except Exception as e:
            print(f'error: {e.__class__.__name__}: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        print(f'error: unknown command: {command!r}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    ctx = LingoContext()
    main(ctx)
