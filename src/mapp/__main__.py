import argparse

from mapp.spec import load_spec
from mapp.module import cli as module_cli


def main():
    spec = load_spec()

    parser = argparse.ArgumentParser(description='mapp CLI (Python template app)')
    subparsers = parser.add_subparsers(dest='module', required=True)

    # For each module in the spec, add a subparser
    for module_name, module in spec.get('modules', {}).items():
        module_cli.add_module_subparser(subparsers, module_name, module)

    args = parser.parse_args()
    # Placeholder: just print the parsed args for now
    print(args)

if __name__ == "__main__":
    main()
