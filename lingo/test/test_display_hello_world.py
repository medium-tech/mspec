import os
import platform
import sys
import time
import unittest

from pathlib import Path
from unittest.mock import patch

from mtester import api
from mtester.context import MTesterContext

WINDOW_TITLE_TEXT_SPEC = 'Lingo Text Spec'
WINDOW_TITLE_GUI_SPEC = 'Lingo GUI Spec'

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

    #
    # text specs
    #

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_hello_text_1(self):
        spec_path = Path('lingo/shared/scripts/text/hello-text.yaml').resolve()
        ctx = MTesterContext(verbose=False)
        ctx.set_test_dir(test_name='test_display_hello_text_1', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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
            self.assertIn('world', ocr_result.text.lower())

        finally:
            session_result = api.stop_target(ctx, session_id=launch_result.session_id)

        self.assertIsNotNone(session_result)
        self.assertTrue(session_result.ok, msg=str(session_result))
        self.assertIn('hello.world', session_result.stderr)

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_hello_text_2(self):
        spec_path = Path('lingo/shared/scripts/text/hello-text-2.yaml').resolve()
        ctx = MTesterContext(verbose=False)
        ctx.set_test_dir(test_name='test_display_hello_text_2', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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

            #
            # ocr text output
            #

            expected_texts = [
                'Text Formatting',
                'A Simple Example',
                'rich text document',
                'line breaks'
            ]
            ocr_text_lower = ocr_result.text.lower()
            for expected_text in expected_texts:
                self.assertIn(expected_text.lower(), ocr_text_lower, msg=f"Expected OCR text '{expected_text}' not found in output")

            #
            # text vertical placement
            #

            # get first word of each line #

            line_1_word_1 = ocr_result.tokens[0]
            line_2_word_1 = ocr_result.tokens[2]
            line_3_word_1 = ocr_result.tokens[5]
            line_4_word_1 = ocr_result.tokens[20]

            assert line_1_word_1.text.lower() == 'text', f"Expected first word of line 1 to be 'Text', got '{line_1_word_1.text}'"
            assert line_2_word_1.text.lower() == 'a', f"Expected first word of line 2 to be 'A', got '{line_2_word_1.text}'"
            assert line_3_word_1.text.lower() == 'this', f"Expected first word of line 3 to be 'rich', got '{line_3_word_1.text}'"
            assert line_4_word_1.text.lower() == 'line', f"Expected first word of line 4 to be 'line', got '{line_4_word_1.text}'"

            # confirm each line is placed beneath the previous line #

            self.assertGreater(line_2_word_1.top, line_1_word_1.top, msg=f"Expected line 2 top value to be greater than line 1 top value, got {line_2_word_1.top=} & {line_1_word_1.top}")
            self.assertGreater(line_3_word_1.top, line_2_word_1.top, msg=f"Expected line 3 top value to be greater than line 2 top value, got {line_3_word_1.top=} & {line_2_word_1.top}")
            self.assertGreater(line_4_word_1.top, line_3_word_1.top, msg=f"Expected line 4 top value to be greater than line 3 top value, got {line_4_word_1.top=} & {line_3_word_1.top}")

        finally:
            session_result = api.stop_target(ctx, session_id=launch_result.session_id)

        self.assertIsNotNone(session_result)
        self.assertTrue(session_result.ok, msg=str(session_result))

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_hello_text_3(self):
        spec_path = Path('lingo/shared/scripts/text/hello-text-3.yaml').resolve()
        ctx = MTesterContext(verbose=False)
        ctx.set_test_dir(test_name='test_display_hello_text_3', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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

            #
            # list vertical placement
            #

            list_item_1_word_1 = ocr_result.tokens[28]
            list_item_2_word_1 = ocr_result.tokens[36]
            list_item_3_word_1 = ocr_result.tokens[43]

            assert list_item_1_word_1.text.lower() == 'this', f"Expected first word of list item 1 to be 'this', got '{list_item_1_word_1.text}'"
            assert list_item_2_word_1.text.lower() == 'another', f"Expected first word of list item 2 to be 'another', got '{list_item_2_word_1.text}'"
            assert list_item_3_word_1.text.lower() == 'and', f"Expected first word of list item 3 to be 'and', got '{list_item_3_word_1.text}'"

            self.assertGreater(list_item_2_word_1.top, list_item_1_word_1.top, msg=f"Expected list item 2 top value to be greater than list item 1 top value, got {list_item_2_word_1.top=} & {list_item_1_word_1.top}")
            self.assertGreater(list_item_3_word_1.top, list_item_2_word_1.top, msg=f"Expected list item 3 top value to be greater than list item 2 top value, got {list_item_3_word_1.top=} & {list_item_2_word_1.top}")

            #
            # struct vertical placement
            #

            struct_value_1 = ocr_result.tokens[69]
            struct_value_2 = ocr_result.tokens[71]
            struct_value_3 = ocr_result.tokens[74]
            struct_value_4 = ocr_result.tokens[76]

            assert struct_value_1.text.lower() == 'true', f"Expected first struct value to be 'true', got '{struct_value_1.text}'"
            assert struct_value_2.text == '42', f"Expected second struct value to be '42', got '{struct_value_2.text}'"
            assert struct_value_3.text == '3.14', f"Expected third struct value to be '3.14', got '{struct_value_3.text}'"
            assert struct_value_4.text.lower() == 'hello.world', f"Expected fourth struct value to be 'hello.world', got '{struct_value_4.text}'"

            self.assertGreater(struct_value_2.top, struct_value_1.top, msg=f"Expected struct value 2 top value to be greater than struct value 1 top value, got {struct_value_2.top=} & {struct_value_1.top}")
            self.assertGreater(struct_value_3.top, struct_value_2.top, msg=f"Expected struct value 3 top value to be greater than struct value 2 top value, got {struct_value_3.top=} & {struct_value_2.top}")
            self.assertGreater(struct_value_4.top, struct_value_3.top, msg=f"Expected struct value 4 top value to be greater than struct value 3 top value, got {struct_value_4.top=} & {struct_value_3.top}")
            
        finally:
            session_result = api.stop_target(ctx, session_id=launch_result.session_id)
    
        self.assertIsNotNone(session_result)
        self.assertTrue(session_result.ok, msg=str(session_result))


    #
    # gui specs
    #

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_hello_gui_test(self):
        spec_path = Path('lingo/shared/scripts/gui/hello-gui.yaml').resolve()
        ctx = MTesterContext(verbose=False)
        ctx.set_test_dir(test_name='test_display_hello_gui_test', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = api.get_region_for_window_title(ctx, window_title=WINDOW_TITLE_GUI_SPEC)

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
