import sys

from lingolib import execute_file


HELP = (
    'usage: lingolib [--help] <command> [args]\n'
    '\n'
    'commands:\n'
    '  exe <path>    load, parse, execute an exe spec and print result\n'
    '\n'
    'supported specs: exe\n'
)


def main():
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
    else:
        print(f'error: unknown command: {command!r}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
