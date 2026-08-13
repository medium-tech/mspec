import os
import platform
import unittest
import itertools

from pathlib import Path
from unittest.mock import patch

from mtester import api
from mtester.context import MTesterContext
from mtester.types import ColorRegionAssertion, PixelRGB, RegionBox

WINDOW_TITLE_TEXT_SPEC = 'Lingo Text Spec'
WINDOW_TITLE_GUI_SPEC = 'Lingo GUI Spec'

IS_DARWIN = platform.system() == 'Darwin'
RUN_GUI_TESTS = os.environ.get('RUN_GUI_TESTS', '0') == '1'
QUICK_WINDOW = os.environ.get('QUICK_WINDOW', '0') == '1'
"""
To speed up tkinter tests you can provide QUICK_WINDOW=1 which means we'll only
query the os for the window size one time and re-use it for remaining tests.

It is less reliable but will speed up tests significantly.

It is based on the assumption that the window size and location does not change between tests.

"""

WINDOW_REGION_CACHE: RegionBox | None = None

class TestLingoDisplayRunTimeHelloWorld(unittest.TestCase):

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
            self.window_region = self.get_window_region(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

            frame_result = api.capture_test_frame(
                ctx,
                name='start_frame',
                region=self.window_region,
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
        self.assertIn(':: DEBUG ::', session_result.stderr)

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
            region = self.get_window_region(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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
            # text vertical placement
            #

            # get a unique word from each line #

            line_1_word = ocr_result.find_token('formatting')
            line_2_word = ocr_result.find_token('simple')
            line_3_word = ocr_result.find_token('sample')
            line_4_word = ocr_result.find_token('line')

            self.assertIsNotNone(line_1_word, msg='Could not find token "formatting"')
            self.assertIsNotNone(line_2_word, msg='Could not find token "simple"')
            self.assertIsNotNone(line_3_word, msg='Could not find token "sample"')
            self.assertIsNotNone(line_4_word, msg='Could not find token "line"')

            # confirm each line is placed beneath the previous line #

            self.assertGreater(line_2_word.top, line_1_word.top, msg=f"Expected line 2 top value to be greater than line 1 top value, got {line_2_word.top=} & {line_1_word.top}")
            self.assertGreater(line_3_word.top, line_2_word.top, msg=f"Expected line 3 top value to be greater than line 2 top value, got {line_3_word.top=} & {line_2_word.top}")
            self.assertGreater(line_4_word.top, line_3_word.top, msg=f"Expected line 4 top value to be greater than line 3 top value, got {line_4_word.top=} & {line_3_word.top}")

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
            region = self.get_window_region(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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

            list_item_1_word_1 = ocr_result.find_token('apples')
            list_item_2_word_1 = ocr_result.find_token('potatoes')
            list_item_3_word_1 = ocr_result.find_token('bison')

            self.assertIsNotNone(list_item_1_word_1, msg='Could not find token "apples" for list item 1')
            self.assertIsNotNone(list_item_2_word_1, msg='Could not find token "potatoes" for list item 2')
            self.assertIsNotNone(list_item_3_word_1, msg='Could not find token "bison" for list item 3')

            assert list_item_1_word_1.text.lower() == 'apples', f"Expected first word of list item 1 to be 'apples', got '{list_item_1_word_1.text}'"
            assert list_item_2_word_1.text.lower() == 'potatoes', f"Expected first word of list item 2 to be 'potatoes', got '{list_item_2_word_1.text}'"
            assert list_item_3_word_1.text.lower() == 'bison', f"Expected first word of list item 3 to be 'bison', got '{list_item_3_word_1.text}'"

            self.assertGreater(list_item_2_word_1.top, list_item_1_word_1.top, msg=f"Expected list item 2 top value to be greater than list item 1 top value, got {list_item_2_word_1.top=} & {list_item_1_word_1.top}")
            self.assertGreater(list_item_3_word_1.top, list_item_2_word_1.top, msg=f"Expected list item 3 top value to be greater than list item 2 top value, got {list_item_3_word_1.top=} & {list_item_2_word_1.top}")

            #
            # struct vertical placement
            #

            struct_bool_key = ocr_result.find_token('boolean')
            self.assertIsNotNone(struct_bool_key, msg='Could not find struct key token "boolean"')
            assert struct_bool_key is not None

            struct_value_1 = ocr_result.next_token()

            struct_int_key = ocr_result.find_token('integer')
            self.assertIsNotNone(struct_int_key, msg='Could not find struct key token "integer"')
            assert struct_int_key is not None
            struct_value_2 = ocr_result.next_token()

            struct_float_key = ocr_result.find_token('float')
            self.assertIsNotNone(struct_float_key, msg='Could not find struct key token "float"')
            assert struct_float_key is not None
            struct_value_3 = ocr_result.next_token()

            struct_string_key = ocr_result.find_token('string')
            self.assertIsNotNone(struct_string_key, msg='Could not find struct key token "string"')
            assert struct_string_key is not None
            struct_value_4 = ocr_result.next_token()

            self.assertIsNotNone(struct_value_1, msg='Could not find value token after "boolean"')
            self.assertIsNotNone(struct_value_2, msg='Could not find value token after "integer"')
            self.assertIsNotNone(struct_value_3, msg='Could not find value token after "float"')
            self.assertIsNotNone(struct_value_4, msg='Could not find value token after "string"')

            assert struct_value_1 is not None
            assert struct_value_2 is not None
            assert struct_value_3 is not None
            assert struct_value_4 is not None

            assert struct_value_1.text.lower() == 'true', f"Expected first struct value to be 'true', got '{struct_value_1.text}'"
            assert struct_value_2.text == '42', f"Expected second struct value to be '42', got '{struct_value_2.text}'"
            assert struct_value_3.text == '3.14', f"Expected third struct value to be '3.14', got '{struct_value_3.text}'"
            assert struct_value_4.text.lower() == 'hello', f"Expected fourth struct value to be 'hello', got '{struct_value_4.text}'"

            self.assertGreater(struct_value_2.top, struct_value_1.top, msg=f"Expected struct value 2 top value to be greater than struct value 1 top value, got {struct_value_2.top=} & {struct_value_1.top}")
            self.assertGreater(struct_value_3.top, struct_value_2.top, msg=f"Expected struct value 3 top value to be greater than struct value 2 top value, got {struct_value_3.top=} & {struct_value_2.top}")
            self.assertGreater(struct_value_4.top, struct_value_3.top, msg=f"Expected struct value 4 top value to be greater than struct value 3 top value, got {struct_value_4.top=} & {struct_value_3.top}")

            #
            # link blue color detection
            #

            # raw url
            https_filter = lambda token: not token.text.lower().startswith('https')
            raw_link_token = next(itertools.dropwhile(https_filter, ocr_result.tokens), None)

            ocr_result.seek_token(0)

            # example of link with text "Wikipedia"
            text_link_token = ocr_result.find_token('wikipedia')

            # word that is not a link
            basic_token = ocr_result.find_token('basic')

            self.assertIsNotNone(raw_link_token, msg='Could not find token for raw link starting with "https" in OCR tokens')
            self.assertIsNotNone(text_link_token, msg='Could not find token for "Wikipedia" in OCR tokens')
            self.assertIsNotNone(basic_token, msg='Could not find token for "basic" in OCR tokens')

            color_result = api.assert_colors_in_regions(
                ctx,
                image_path=capture_result.image_path,
                color_assertions=[
                    ColorRegionAssertion(
                        name='raw_link_has_blue',
                        region=raw_link_token.get_region_box(),
                        color=PixelRGB(r=0, g=0, b=255),
                        expected_present=True,
                        tolerance=110,
                    ),
                    ColorRegionAssertion(
                        name='wikipedia_text_link_has_blue',
                        region=text_link_token.get_region_box(),
                        color=PixelRGB(r=0, g=0, b=255),
                        expected_present=True,
                        tolerance=110,
                    ),
                    ColorRegionAssertion(
                        name='basic_has_no_blue',
                        region=basic_token.get_region_box(),
                        color=PixelRGB(r=0, g=0, b=255),
                        expected_present=False,
                        tolerance=110,
                    ),
                ],
            )

            self.assertTrue(color_result.ok, msg=str(color_result))
            self.assertEqual(len(color_result.assertions), 3, msg=f"Expected 3 color assertions, got {len(color_result.assertions)}")
            self.assertTrue(color_result.assertions[0].passed, msg=str(color_result.assertions[0]))
            self.assertTrue(color_result.assertions[1].passed, msg=str(color_result.assertions[1]))
            self.assertTrue(color_result.assertions[2].passed, msg=str(color_result.assertions[2]))

        finally:
            session_result = api.stop_target(ctx, session_id=launch_result.session_id)
    
        self.assertIsNotNone(session_result)
        self.assertTrue(session_result.ok, msg=str(session_result))

    @unittest.skipUnless(IS_DARWIN and RUN_GUI_TESTS, 'display smoke tests are macOS-only and require RUN_GUI_TESTS=1')
    def test_display_text_styles(self):
        spec_path = Path('lingo/shared/scripts/text/text-styles.yaml').resolve()
        ctx = MTesterContext(verbose=False)
        ctx.set_test_dir(test_name='test_display_text_styles', reset=True)

        launch_result = api.launch_target(
            ctx,
            command=['python', '-m', 'lingolib', '-v', 'display', spec_path],
        )
        self.assertTrue(launch_result.ok, msg=str(launch_result))

        try:
            region = self.get_window_region(ctx, window_title=WINDOW_TITLE_TEXT_SPEC)

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
            # text line order
            #

            word_text = ocr_result.find_token('text')
            word_decorations = ocr_result.find_token('decorations')
            word_aardvark = ocr_result.find_token('aardvark')
            word_thistle = ocr_result.find_token('thistle')
            word_rainbow = ocr_result.find_token('rainbow')
            word_red = ocr_result.find_token('red')
            word_print = ocr_result.find_token('print')
            word_magenta = ocr_result.find_token('magenta') # use magenta because its color is more reliable for OCR than cyan
            word_shades = ocr_result.find_token('shades')
            word_white = ocr_result.find_token('white')

            self.assertIsNotNone(word_text, msg='Could not find token "Text"')
            self.assertIsNotNone(word_decorations, msg='Could not find token "Decorations"')
            self.assertIsNotNone(word_aardvark, msg='Could not find token "aardvark"')
            self.assertIsNotNone(word_thistle, msg='Could not find token "thistle"')
            self.assertIsNotNone(word_rainbow, msg='Could not find token "Rainbow"')
            self.assertIsNotNone(word_red, msg='Could not find token "red"')
            self.assertIsNotNone(word_print, msg='Could not find token "print"')
            self.assertIsNotNone(word_magenta, msg='Could not find token "magenta"')
            self.assertIsNotNone(word_shades, msg='Could not find token "shades"')
            self.assertIsNotNone(word_white, msg='Could not find token "white"')

            self.assertGreater(word_decorations.top, word_text.top, msg=f'Expected "Decorations" to be lower than "Text", got {word_decorations.top=} & {word_text.top=}')
            self.assertGreater(word_aardvark.top, word_decorations.top, msg=f'Expected "aardvark" to be lower than "Decorations", got {word_aardvark.top=} & {word_decorations.top=}')
            self.assertGreater(word_thistle.top, word_aardvark.top, msg=f'Expected "thistle" to be lower than "aardvark", got {word_thistle.top=} & {word_aardvark.top=}')
            self.assertGreater(word_rainbow.top, word_thistle.top, msg=f'Expected "Rainbow" to be lower than "thistle", got {word_rainbow.top=} & {word_thistle.top=}')
            self.assertGreater(word_red.top, word_rainbow.top, msg=f'Expected "red" to be lower than "Rainbow", got {word_red.top=} & {word_rainbow.top=}')
            self.assertGreater(word_print.top, word_red.top, msg=f'Expected "print" to be lower than "red", got {word_print.top=} & {word_red.top=}')
            self.assertGreater(word_magenta.top, word_print.top, msg=f'Expected "magenta" to be lower than "print", got {word_magenta.top=} & {word_print.top=}')
            self.assertGreater(word_shades.top, word_magenta.top, msg=f'Expected "shades" to be lower than "magenta", got {word_shades.top=} & {word_magenta.top=}')
            self.assertGreater(word_white.top, word_shades.top, msg=f'Expected "white" to be lower than "shades", got {word_white.top=} & {word_shades.top=}')

            #
            # text colors
            #

            ocr_result.seek_token(0)

            red_token = ocr_result.find_token('red')
            green_token = ocr_result.find_token('green')
            blue_token = ocr_result.find_token('blue')

            self.assertIsNotNone(red_token, msg='Could not find token "red" for color assertion')
            self.assertIsNotNone(green_token, msg='Could not find token "green" for color assertion')
            self.assertIsNotNone(blue_token, msg='Could not find token "blue" for color assertion')

            color_result = api.assert_colors_in_regions(
                ctx,
                image_path=capture_result.image_path,
                color_assertions=[
                    ColorRegionAssertion(
                        name='red_word_has_red',
                        region=red_token.get_region_box(),
                        color=PixelRGB(r=255, g=0, b=0),
                        expected_present=True,
                        tolerance=120,
                    ),
                    ColorRegionAssertion(
                        name='green_word_has_green',
                        region=green_token.get_region_box(),
                        color=PixelRGB(r=0, g=128, b=0),
                        expected_present=True,
                        tolerance=120,
                    ),
                    ColorRegionAssertion(
                        name='blue_word_has_blue',
                        region=blue_token.get_region_box(),
                        color=PixelRGB(r=0, g=0, b=255),
                        expected_present=True,
                        tolerance=120,
                    )
                ],
            )

            self.assertTrue(color_result.ok, msg=str(color_result))
            self.assertEqual(len(color_result.assertions), 3, msg=f'Expected 3 color assertions, got {len(color_result.assertions)}')
            self.assertTrue(color_result.assertions[0].passed, msg=str(color_result.assertions[0]))
            self.assertTrue(color_result.assertions[1].passed, msg=str(color_result.assertions[1]))
            self.assertTrue(color_result.assertions[2].passed, msg=str(color_result.assertions[2]))

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
            region = self.get_window_region(ctx, window_title=WINDOW_TITLE_GUI_SPEC)

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
