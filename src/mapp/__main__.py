import argparse

from mapp.spec import load_spec_from_env
from mapp.module import cli as module_cli


def main():
    spec = load_spec_from_env()

    parser = argparse.ArgumentParser(description='mapp CLI (Python template app)')
    subparsers = parser.add_subparsers(dest='module', help='Available modules')
    

    # For each module in the spec, add a subparser
    for module in spec.get('modules', {}).values():
        module_cli.add_module_subparser(subparsers, module)

    args = parser.parse_args()

    if args.module is None:
        parser.print_help()
        return


    # Placeholder: just print the parsed args for now
    print(args)

if __name__ == "__main__":
    main()
