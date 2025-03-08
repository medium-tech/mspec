import argparse

parser = argparse.ArgumentParser(description='core cli')
parser.add_argument('command', choices=['gui'], help='command to run')
parser.add_argument('--start-frame', help='start frame for gui', default='MSpecIndexPage')
args = parser.parse_args()

if args.command == 'gui':
    from core.gui import gui_main
    gui_main(args.start_frame)

elif args.command == 'setup':
    from core.db import create_db_context, create_db_tables
    db_ctx = create_db_context()
    create_db_tables(db_ctx)

else:
    parser.print_help()
