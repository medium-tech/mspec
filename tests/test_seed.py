import json
import sys
import types
import unittest

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


if __name__ == '__main__':
    unittest.main()
