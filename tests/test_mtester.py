import os
import platform
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from mtester.context import MTesterContext
from mtester.ops import manual_flow
from mtester.types import ManualFlowOptions

IS_DARWIN = platform.system() == 'Darwin'
RUN_GUI_TESTS = os.environ.get('RUN_GUI_TESTS', '0') == '1'


class TestMTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

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
        )

        ctx.set_test_dir(test_name='test_manual_flow_finds_ocr_text', reset=True)

        result = manual_flow(ctx, options, wait_for_window=0.0)

        self.assertIn('assert_ocr_text', result)
        for case in result['assert_ocr_text']:
            self.assertTrue(case['found'], f"Expected OCR text '{case['text']}' not found in output")

        self.assertIn('assert_not_ocr_text', result)
        for case in result['assert_not_ocr_text']:
            self.assertTrue(case['not_found'], f"Unexpected OCR text '{case['text']}' was found in output")
