import os
import platform
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from mtester.context import MTesterConfig, MTesterContext
from mtester.ops import manual_flow


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

    @unittest.skipUnless(platform.system() == 'Darwin', 'manual_flow smoke tests are macOS-only')
    def test_manual_flow_finds_ocr_text(self):
        ctx = MTesterContext(
            config=MTesterConfig(
                spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
                window_title='Lingo GUI Spec',
                assert_ocr_text=['total',  'count'],
                verbose=False,
            )
        )

        ctx.set_test_dir(test_name='test_manual_flow_finds_ocr_text', reset=True)

        with patch.dict(
            os.environ,
            {'PATH': f'{Path(sys.executable).parent}:{os.environ.get("PATH", "")}'},
            clear=False,
        ):
            result = manual_flow(ctx, wait_for_window=0.0)

        self.assertIn('assert_ocr_text', result)
        for case in result['assert_ocr_text']:
            self.assertTrue(case['found'], f"Expected OCR text '{case['text']}' not found in output")

    @unittest.skipUnless(platform.system() == 'Darwin', 'manual_flow smoke tests are macOS-only')
    def test_manual_flow_finds_stderr_text(self):
        ctx = MTesterContext(
            config=MTesterConfig(
                spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
                window_title='Lingo GUI Spec',
                assert_stderr=['lingo'],
                verbose=False,
            )
        )
        ctx.set_test_dir(test_name='test_manual_flow_finds_stderr_text', reset=True)
        with patch.dict(
            os.environ,
            {'PATH': f'{Path(sys.executable).parent}:{os.environ.get("PATH", "")}'},
            clear=False,
        ):
            result = manual_flow(ctx, wait_for_window=0.0)

        self.assertIn('assert_stderr', result)
        for case in result['assert_stderr']:
            self.assertTrue(case['found'], f"Expected stderr text '{case['text']}' not found in output")

