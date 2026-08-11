import os
import platform
import sys
import time
import unittest

from pathlib import Path
from unittest.mock import patch

from mtester import api
from mtester.context import MTesterConfig, MTesterContext
from mtester.types import RegionBox

WINDOW_TITLE = 'Lingo GUI Spec'

IS_DARWIN = platform.system() == 'Darwin'
RUN_GUI_TESTS = os.environ.get('RUN_GUI_TESTS', '0') == '1'

class TestLingoDisplayRunTimeHelloWorld(unittest.TestCase):

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

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_hello_gui_test(self):
        ctx = MTesterContext(
            config=MTesterConfig(
                spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
                window_title=WINDOW_TITLE,
                verbose=False,
            )
        )
        ctx.set_test_dir(test_name='test_display_hello_gui_test', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', ctx.config.spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE)

            frame_result = api.capture_test_frame(
                ctx,
                name='start_frame',
                region=region,
                wait_for_window=0.5,
                extract_ocr=True,
            )
            capture_result = frame_result.capture_result
            ocr_result = frame_result.ocr_result

            self.assertTrue(capture_result.ok, msg=str(capture_result))
            self.assertIsNotNone(ocr_result)
            self.assertTrue(ocr_result.ok, msg=str(ocr_result))
            self.assertIn('total count', ocr_result.text.lower())

        finally:
            session_result = api.stop_target(ctx, session_id=launch_result.session_id)

        self.assertIsNotNone(session_result)
        self.assertTrue(session_result.ok, msg=str(session_result))
        self.assertIn(':: DEBUG ::', session_result.stderr)
