#
# mtester cli
#

import argparse
import json

from mtester import ops
from mtester.ops import manual_flow


def json_print(data) -> None:
    print(json.dumps(data, indent=4, sort_keys=True))


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='mtester: application testing with image OCR and color detection'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    identify_parser = subparsers.add_parser('identify', help='Identify image properties')
    identify_parser.add_argument('source', help='Path to the source image')

    manual_parser = subparsers.add_parser(
        'manual',
        help='Run a manual PoC test flow against a lingo spec (window list/select is macOS-only for now)'
    )
    manual_parser.add_argument('spec', help='Path to lingo spec file')
    manual_parser.add_argument('--window-title', dest='window_title', help='Window title to select (currently only OSX)')
    manual_parser.add_argument('--select-window', dest='select_window', action='store_true', help='Select a window from the list of open windows (currently only OSX)')
    manual_parser.add_argument('--capture-region', dest='capture_region', help='Capture region in format x,y,width,height (cannot supply w/ --select-window)')
    manual_parser.add_argument('--assert-ocr-text', dest='assert_ocr_text', help='Assert text appears in OCR output')
    manual_parser.add_argument('--assert-stdout', dest='assert_stdout', help='Assert text appears in target stdout')
    manual_parser.add_argument('--assert-stderr', dest='assert_stderr', help='Assert text appears in target stderr')
    manual_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    if args.command == 'identify':
        result = ops.identify(args.source)
        json_print(result)
        return

    elif args.command == 'manual':
        result = manual_flow(args)
        json_print(result)
        return
    else:
        raise RuntimeError(f'Unsupported command: {args.command!r}')
