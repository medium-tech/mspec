#
# mtester main entrypoint
#

import json
import argparse

from mtester import ops

def json_print(data) -> None:
    """Utility function to print data as formatted JSON."""
    print(json.dumps(data, indent=4, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(
        description='mtester: application testing with image OCR and color detection'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    identify_parser = subparsers.add_parser('identify', help='Identify image properties')
    identify_parser.add_argument('source', help='Path to the source image')
    
    args = parser.parse_args()

    if args.command == 'identify':
        result = ops.identify(args.source)
        json_print(result)


if __name__ == '__main__':
    main()
