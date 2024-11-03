import argparse

parser = argparse.ArgumentParser(description='core cli')
parser.add_argument('command', choices=['gui', 'hello', 'form', 'pages'], help='command to run')
args = parser.parse_args()

if args.command == 'gui':
    from core.gui import main
    main()
elif args.command == 'hello':
    from core.gui import hello
    hello()
elif args.command == 'form':
    from core.gui import form
    form()
elif args.command == 'pages':
    from core.gui import pages
    pages()
else:
    parser.print_help()