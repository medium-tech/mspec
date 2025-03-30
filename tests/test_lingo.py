import unittest
import datetime

from pprint import pprint

from lingo.expressions import *

class TestLingoApp(unittest.TestCase):

    def test_example_app_first_visit(self):
        app = LingoApp.init(example_spec, first_visit=True)
        app.state['name'] = 'Alice'
        doc = render_document(app)

        greeting = doc[14]['text']
        self.assertEqual(greeting, 'Welcome in, ')

        name = doc[15]['text']
        self.assertEqual(name, 'Alice')

        self._test_doc(doc)

    def test_example_app_not_first_visit(self):
        app = LingoApp.init(example_spec, first_visit=False)
        app.state['name'] = 'Bob'
        doc = render_document(app)

        greeting = doc[14]['text']
        self.assertEqual(greeting, 'Welcome back, ')

        name = doc[15]['text']
        self.assertEqual(name, 'Bob')
        
        self._test_doc(doc)

    def _test_doc(self, doc:list[dict]):      
        self.assertIsInstance(doc, list)

        # for n, element in enumerate(doc):
        #     print(n, element)

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
