import json
import sys
import types
import unittest
from unittest.mock import patch

from mspec.core import validate_rich_text_json_string

if 'PIL' not in sys.modules:
    pil_stub = types.ModuleType('PIL')
    pil_stub.Image = object()
    pil_stub.ImageDraw = object()
    sys.modules['PIL'] = pil_stub

from mspec.seed import random_str_rich_text


class TestSeedRandomGenerators(unittest.TestCase):

    def test_random_str_rich_text_returns_valid_rich_text_json(self):
        for _ in range(20):
            rich_text_json = random_str_rich_text()
            rich_text = json.loads(rich_text_json)

            self.assertEqual(rich_text['lingo']['version'], 'rich-text-beta-1')
            self.assertGreaterEqual(len(rich_text['block']), 1)
            self.assertEqual(rich_text, validate_rich_text_json_string(rich_text_json))

    def test_random_str_rich_text_adds_spaces_between_sentences(self):
        # randint side_effect order:
        # [num_sentences, sentence_1_word_count, sentence_1_color_flag, sentence_1_break_flag,
        #  sentence_2_word_count, sentence_2_color_flag]
        with patch('mspec.seed.random.randint', side_effect=[2, 3, 1, 1, 3, 1]), \
             patch('mspec.seed.random_bool', return_value=False), \
             patch('mspec.seed.random.choices', return_value=['lion', 'apple', 'sad']):
            rich_text_json = random_str_rich_text()

        rich_text = json.loads(rich_text_json)
        self.assertEqual(len(rich_text['block']), 2)
        self.assertEqual(rich_text['block'][0]['text'], 'Lion apple sad. ')
        self.assertEqual(rich_text['block'][1]['text'], 'Lion apple sad.')


if __name__ == '__main__':
    unittest.main()
