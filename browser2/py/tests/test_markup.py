import unittest
import datetime
import json

from pprint import pprint
from pathlib import Path
from mspec.markup import *

test_spec_path = Path(__file__).parent.parent.parent.parent / 'src/mspec/data/test-page.json'

with open(test_spec_path, 'r') as f:
    test_spec = json.load(f)

class TestLingoApp(unittest.TestCase):

    def test_example_app_first_visit(self):
        app = lingo_app(test_spec, first_visit=True)
        app.state['name'] = 'Alice'
        doc = render_output(app)

        greeting = doc[14]['text']
        self.assertEqual(greeting, 'Welcome in, ')

        name = doc[15]['text']
        self.assertEqual(name, 'Alice')

        self._test_doc(doc, debug=False)

    def test_example_app_not_first_visit(self):
        app = lingo_app(test_spec, first_visit=False)
        app.state['name'] = 'Bob'
        doc = render_output(app)

        greeting = doc[14]['text']
        self.assertEqual(greeting, 'Welcome back, ')

        name = doc[15]['text']
        self.assertEqual(name, 'Bob')
        
        self._test_doc(doc, debug=False)

    def _test_doc(self, doc:list[dict], debug=False):      
        self.assertIsInstance(doc, list)

        if debug:
            for n, element in enumerate(doc):
                print(n, element)
            keys = []
            for element in doc:
                keys.extend(element.keys())
            keys = set(keys)
            pprint(keys)

        heading = doc[0]
        self.assertEqual(heading['heading'], 'Example document')
        self.assertEqual(heading['level'], 1)

        timestamp = datetime.fromisoformat(doc[2]['text'])
        self.assertIsInstance(timestamp, datetime)

        self.assertIn(doc[9]['text'], ['0', '1'])

        when = doc[19]['text']
        weekday = datetime.now().weekday()
        expecting = 'Weekend'
        if weekday == 0:
            expecting = 'Monday'
        elif weekday == 1:
            expecting = 'Tuesday'
        elif weekday == 2:
            expecting = 'Wednesday'
        elif weekday == 3:
            expecting = 'Thursday'
        elif weekday == 4:
            expecting = 'Friday'

        self.assertEqual(when, expecting, f"Expected {expecting} but got {when} based on weekday {weekday}")

if __name__ == '__main__':
    unittest.main()
