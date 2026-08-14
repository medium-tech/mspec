import os
import platform
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from mtester.context import MTesterContext
from mtester import api
from mtester.ops import manual_flow
from mtester.types import ManualFlowOptions, RegionBox

IS_DARWIN = platform.system() == 'Darwin'
RUN_GUI_TESTS = os.environ.get('RUN_GUI_TESTS', '0') == '1'
QUICK_WINDOW = os.environ.get('QUICK_WINDOW', '0') == '1'

WINDOW_REGION_CACHE: RegionBox | None = None

if QUICK_WINDOW:
    config_path = Path.cwd() / '.mtester' / 'config.json'
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        WINDOW_REGION_CACHE = RegionBox(**config_data['window_region'])


class TestMTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass
    def get_window_region(self, ctx, window_title:str) -> RegionBox:
        global WINDOW_REGION_CACHE

        # print(f'\n\tget_window_region: {WINDOW_REGION_CACHE=} {QUICK_WINDOW=} {window_title=}')
        
        if WINDOW_REGION_CACHE is None or not QUICK_WINDOW:
            # print(f'\t\tget_window_region: querying os for window region for title')
            WINDOW_REGION_CACHE = api.get_region_for_window_title(ctx, window_title=window_title)

        # print(f'\t\tget_window_region: returning window region {WINDOW_REGION_CACHE=}')
        return WINDOW_REGION_CACHE
    
    def test_can_import_mtester(self):
        import mtester
        self.assertIsNotNone(mtester)

    def test_can_import_lingolib(self):
        import lingolib
        self.assertIsNotNone(lingolib)

        from lingolib.context import init_logger
        self.assertIsNotNone(init_logger)

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'manual flow tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_manual_flow_finds_ocr_text(self):
        ctx = MTesterContext(verbose=False)
        options = ManualFlowOptions(
            spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
            window_title='Lingo GUI Spec',
            assert_ocr_text=['total', 'count'],
            assert_not_ocr_text=['peanut butter'],
            verbose=False,
            capture_region=self.get_window_region(ctx, window_title='Lingo GUI Spec'),
        )

        ctx.set_test_dir(test_name='test_manual_flow_finds_ocr_text', reset=True)

        result = manual_flow(ctx, options, wait_for_window=0.0)

        self.assertIn('assert_ocr_text', result)
        for case in result['assert_ocr_text']:
            self.assertTrue(case['found'], f"Expected OCR text '{case['text']}' not found in output")

        self.assertIn('assert_not_ocr_text', result)
        for case in result['assert_not_ocr_text']:
            self.assertTrue(case['not_found'], f"Unexpected OCR text '{case['text']}' was found in output")
