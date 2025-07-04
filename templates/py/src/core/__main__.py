import argparse

parser = argparse.ArgumentParser(description='core cli')
parser.add_argument('command', choices=['gui'], help='command to run')
parser.add_argument('--start-frame', help='start frame for gui', default='MSpecIndexPage')
parser.add_argument('--reload', action='store_true', help='reload gui on ctr+c for development (not working yet, i guess tkinter suppresses the signal?)')
args = parser.parse_args()

if args.command == 'gui':
    import importlib
    import core.gui
    while True:
        # print('dummy check')
        try:
            importlib.reload(core.gui)
            core.gui.gui_main(args.start_frame)
            print('main exited')

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received.")
            if args.reload:
                print("Reloading GUI...")
                continue
            else:
                print("Exiting GUI...")
                break
        
elif args.command == 'setup':
    from core.db import create_db_context, create_db_tables
    db_ctx = create_db_context()
    create_db_tables(db_ctx)

else:
    parser.print_help()