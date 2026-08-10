import argparse

from pathlib import Path

from mtester.context import MTesterConfig, MTesterContext
from mtester.ops import manual_flow
from mtester.types import RegionBox, json_pprint


def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description='mtester: application testing with image OCR and color detection'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

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

def create_context(args: argparse.Namespace) -> MTesterContext:

    if args.capture_region and args.select_window:
        raise RuntimeError('Cannot supply both --capture-region and --select-window')

    if args.capture_region:
        x, y, width, height = map(int, args.capture_region.split(','))
        capture_region = RegionBox(x=x, y=y, width=width, height=height)
    else:
        capture_region = None

    new_ctx = MTesterContext(
        config=MTesterConfig(
            spec_path=Path(args.spec).resolve(),
            capture_region=capture_region,
            window_title=args.window_title,
            select_window=args.select_window,
            assert_ocr_text=args.assert_ocr_text,
            assert_stdout=args.assert_stdout,
            assert_stderr=args.assert_stderr,
            verbose=args.verbose
        )
    )

    return new_ctx

def main(argv: list[str] | None = None):
    args = parse_args(argv)
    ctx = create_context(args)
    if args.command == 'manual':
        result = manual_flow(ctx)
        print(json_pprint(result))
        return
    else:
        raise RuntimeError(f'Unsupported command: {args.command!r}')
