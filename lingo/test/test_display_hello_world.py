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

    @unittest.skipUnless(platform.system() == 'Darwin', 'display smoke tests are macOS-only')
    def test_display_hello_gui_finds_ocr_text_via_api(self):
        ctx = MTesterContext(
            config=MTesterConfig(
                spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
                window_title=WINDOW_TITLE,
                verbose=False,
            )
        )
        ctx.set_test_dir(test_name='test_display_hello_gui_finds_ocr_text_via_api', reset=True)

        launch_result = None
        stop_result = None

        with patch.dict(
            os.environ,
            {'PATH': f'{Path(sys.executable).parent}:{os.environ.get("PATH", "")}'},
            clear=False,
        ):
            launch_result = api.launch_target(
                ctx,
                command=['python', '-m', 'lingolib', '-v', 'display', ctx.config.spec_path],
            )
            self.assertTrue(launch_result.get('ok', False))

            try:
                time.sleep(0.5)

                capture_region = None
                windows_result = api.list_windows(ctx)
                if windows_result.get('ok'):
                    windows = windows_result.get('windows', [])
                    filtered_windows = [w for w in windows if ctx.config.window_title == w['title']]
                    self.assertEqual(
                        len(filtered_windows),
                        1,
                        f'Expected exactly one window matching title: {ctx.config.window_title!r}, found {len(filtered_windows)}',
                    )
                    selected_window = filtered_windows[0]
                    capture_region = RegionBox(
                        x=selected_window['x'],
                        y=selected_window['y'],
                        width=selected_window['width'],
                        height=selected_window['height'],
                    )

                image_path = ctx.test_dir / 'test_frame.png'
                capture_result = api.capture_screen(ctx, output_path=image_path, region=capture_region)
                self.assertTrue(capture_result.get('ok', False), msg=str(capture_result))

                ocr_result = api.ocr_extract(ctx, image_path=image_path)
                self.assertTrue(ocr_result.get('ok', False), msg=str(ocr_result))

                ocr_text = str(ocr_result.get('text', '')).lower()
                for expected_ocr_text in ['total', 'count']:
                    self.assertIn(expected_ocr_text, ocr_text)
                for unexpected_ocr_text in ['peanut butter']:
                    self.assertNotIn(unexpected_ocr_text, ocr_text)

            finally:
                if launch_result and launch_result.get('session_id'):
                    stop_result = api.stop_target(ctx, session_id=launch_result['session_id'])
                    self.assertTrue(stop_result.get('ok', False), msg=str(stop_result))

    @unittest.skipUnless(platform.system() == 'Darwin', 'display smoke tests are macOS-only')
    def test_display_hello_gui_finds_stderr_text_via_api(self):
        ctx = MTesterContext(
            config=MTesterConfig(
                spec_path=Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve(),
                window_title=WINDOW_TITLE,
                verbose=False,
            )
        )
        ctx.set_test_dir(test_name='test_display_hello_gui_finds_stderr_text_via_api', reset=True)

        launch_result = None
        stop_result = None

        with patch.dict(
            os.environ,
            {'PATH': f'{Path(sys.executable).parent}:{os.environ.get("PATH", "")}'},
            clear=False,
        ):
            launch_result = api.launch_target(
                ctx,
                command=['python', '-m', 'lingolib', '-v', 'display', ctx.config.spec_path],
            )
            self.assertTrue(launch_result.get('ok', False))

            try:
                time.sleep(0.5)

                capture_region = None
                windows_result = api.list_windows(ctx)
                if windows_result.get('ok'):
                    windows = windows_result.get('windows', [])
                    filtered_windows = [w for w in windows if ctx.config.window_title == w['title']]
                    self.assertEqual(
                        len(filtered_windows),
                        1,
                        f'Expected exactly one window matching title: {ctx.config.window_title!r}, found {len(filtered_windows)}',
                    )
                    selected_window = filtered_windows[0]
                    capture_region = RegionBox(
                        x=selected_window['x'],
                        y=selected_window['y'],
                        width=selected_window['width'],
                        height=selected_window['height'],
                    )

                image_path = ctx.test_dir / 'test_frame.png'
                capture_result = api.capture_screen(ctx, output_path=image_path, region=capture_region)
                self.assertTrue(capture_result.get('ok', False), msg=str(capture_result))

            finally:
                if launch_result and launch_result.get('session_id'):
                    stop_result = api.stop_target(ctx, session_id=launch_result['session_id'])
                    self.assertTrue(stop_result.get('ok', False), msg=str(stop_result))

        stderr_text = str((stop_result or {}).get('stderr', '')).lower()
        for expected_stderr_text in ['lingo']:
            self.assertIn(expected_stderr_text, stderr_text)
        for unexpected_stderr_text in ['peanut butter']:
            self.assertNotIn(unexpected_stderr_text, stderr_text)
