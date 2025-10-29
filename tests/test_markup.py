import unittest
import datetime
import json

from pprint import pprint
from mspec import load_browser2_spec, sample_browser2_spec_dir, builtin_spec_files, load_lingo_script_spec
from mspec.markup import *


class TestLingoPages(unittest.TestCase):
        
    @classmethod
    def setUpClass(cls):
        cls.test_spec_path = sample_browser2_spec_dir / 'test-page.json'
        cls.functions_spec_path = sample_browser2_spec_dir / 'functions.json'

        with open(cls.test_spec_path, 'r') as f:
            cls.test_spec = json.load(f)

        with open(cls.functions_spec_path, 'r') as f:
            cls.functions_spec = json.load(f)

    def test_example_app_first_visit(self):
        app = lingo_app(self.test_spec, first_visit=True)
        app.state['name'] = 'Alice'
        doc = render_output(app)

        self.assertEqual(doc[16]['text'], 'Welcome in, ')
        self.assertEqual(doc[17]['text'], 'Alice')

        self._test_doc(doc, debug=False)

    def test_example_app_not_first_visit(self):
        app = lingo_app(self.test_spec, first_visit=False)
        app.state['name'] = 'Bob'
        doc = render_output(app)
        
        self.assertEqual(doc[16]['text'], 'Welcome back, ')
        self.assertEqual(doc[17]['text'], 'Bob')
        
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

        when = doc[21]['text']
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

    def test_all_functions_coverage(self):
        """Verify that all functions in lingo_function_lookup are tested"""
        
        # Get all function names from lingo_function_lookup
        expected_functions = set()
        for key, value in lingo_function_lookup.items():
            if isinstance(value, dict) and 'func' in value:
                expected_functions.add(key)
            elif isinstance(value, dict):
                # Nested functions like current.weekday, datetime.now, random.randint
                for subkey in value.keys():
                    expected_functions.add(f"{key}.{subkey}")
        
        # Check that we have state variables or direct calls for each function
        tested_functions = set()
        
        # Check state calculations for tested functions
        for state_key, state_def in self.functions_spec['state'].items():
            if 'calc' in state_def and 'call' in state_def['calc']:
                tested_functions.add(state_def['calc']['call'])
        
        # Check output for direct function calls
        def check_calls_in_element(element):
            if isinstance(element, dict):
                if 'call' in element:
                    tested_functions.add(element['call'])
                for value in element.values():
                    if isinstance(value, (dict, list)):
                        check_calls_in_element(value)
            elif isinstance(element, list):
                for item in element:
                    check_calls_in_element(item)

        for output_element in self.functions_spec['output']:
            check_calls_in_element(output_element)
        
        # Verify coverage
        missing_functions = expected_functions - tested_functions
        self.assertEqual(len(missing_functions), 0, 
                        f"Missing tests for functions: {missing_functions}")

    def test_return_types(self):
        spec = load_browser2_spec('return-types.json')
        app = lingo_app(spec)
        doc = render_output(lingo_update_state(app))


    def test_functions_page(self):
        """Test all functions defined in lingo_function_lookup using functions.json"""
        app = lingo_app(self.functions_spec)
        doc = render_output(app)
        
        # Test that we get the expected number of output elements
        self.assertGreater(len(doc), 90, "Should have many output elements for comprehensive function testing")
        
        # Verify it's structured as expected
        heading = doc[0]
        self.assertEqual(heading['heading'], 'Function Tests')
        self.assertEqual(heading['level'], 1)

    def test_boolean_functions(self):
        """Test boolean conversion functions"""
        app = lingo_app(self.functions_spec)
        
        # Test bool function
        self.assertTrue(app.state['test_bool_true'])
        self.assertFalse(app.state['test_bool_false'])
        
        # Test not function
        self.assertFalse(app.state['test_not_true'])
        self.assertTrue(app.state['test_not_false'])
        
        # Test neg function
        self.assertEqual(app.state['test_neg'], -5)

    def test_int_functions(self):
        """Test integer conversion functions"""
        app = lingo_app(self.functions_spec)
        
        # Test int function with number
        self.assertEqual(app.state['test_int'], 42)
        
        # Test int function with string and base
        self.assertEqual(app.state['test_int_base'], 42)

    def test_float_functions(self):
        """Test float conversion functions"""
        app = lingo_app(self.functions_spec)

        # Test float function
        self.assertEqual(app.state['test_float'], 0.001)

        self.assertEqual(app.state['test_round_default'], 3)
        self.assertEqual(app.state['test_round_ndigits'], 3.142)

    def test_string_functions(self):
        """Test string-related functions"""
        app = lingo_app(self.functions_spec)
        
        # Test str function
        self.assertEqual(app.state['test_str'], '123')
        
        # Test join function
        self.assertEqual(app.state['test_join'], 'a-b-c')

    def test_logical_functions(self):
        """Test logical operators"""
        app = lingo_app(self.functions_spec)
        
        # Test and function
        self.assertTrue(app.state['test_and_true'])
        self.assertFalse(app.state['test_and_false'])
        
        # Test or function
        self.assertTrue(app.state['test_or_true'])
        self.assertFalse(app.state['test_or_false'])

    def test_math_functions(self):
        """Test mathematical operators"""
        app = lingo_app(self.functions_spec)
        
        # Test arithmetic
        self.assertEqual(app.state['test_add'], 15)
        self.assertEqual(app.state['test_sub'], 7)
        self.assertEqual(app.state['test_mul'], 28)
        self.assertEqual(app.state['test_div'], 5.0)
        self.assertEqual(app.state['test_pow'], 8)
        self.assertEqual(app.state['test_min'], 3)
        self.assertEqual(app.state['test_max'], 7)
        self.assertEqual(app.state['test_abs'], 10)
        self.assertEqual(app.state['test_floordiv'], 7)
        self.assertEqual(app.state['test_mod'], 3)

    def test_list_functions(self):
        """Test list-related functions"""
        app = lingo_app(self.functions_spec)

        # Test list creation
        self.assertEqual(app.state['test_len_list'], 5)
        self.assertEqual(app.state['test_len_string'], 5)
        self.assertTrue(app.state['test_any_true'])
        self.assertFalse(app.state['test_any_false'])
        self.assertTrue(app.state['test_all_true'])
        self.assertFalse(app.state['test_all_false'])

        self.assertEqual(app.state['test_slice_default'], [0, 1])
        self.assertEqual(app.state['test_slice_start'], [2, 3, 4])
        self.assertEqual(app.state['test_slice_step'], [1, 3])
        self.assertEqual(app.state['test_range_default'], [0, 1, 2, 3, 4])
        self.assertEqual(app.state['test_range_start'], [1, 2, 3, 4, 5, 6])
        self.assertEqual(app.state['test_range_step'], [0, 2, 4, 6, 8])
        self.assertEqual(app.state['test_map'], [11, 12, 13, 14, 15])

        self.assertEqual(app.state['test_filter'], [4, 5, 6, 7])
        self.assertEqual(app.state['test_dropwhile'], [4, 5, 6, 7])
        self.assertEqual(app.state['test_takewhile'], [1, 2, 3])
        self.assertEqual(app.state['test_reversed'], [3, 2, 1])

        self.assertEqual(app.state['test_sum'], 6)
        self.assertEqual(app.state['test_sum_start'], 16)
        self.assertEqual(app.state['test_sorted'], [2, 5, 9])
        self.assertEqual(app.state['test_accumulate'], [1, 3, 6, 10])
        self.assertEqual(app.state['test_accumulate_initial'], [10, 11, 13, 16, 20])
        self.assertEqual(app.state['test_reduce'], 10)
        self.assertEqual(app.state['test_reduce_initial'], 20)
        
    def test_comparison_functions(self):
        """Test comparison operators"""
        app = lingo_app(self.functions_spec)
        
        # Test equality
        self.assertTrue(app.state['test_eq_true'])
        self.assertFalse(app.state['test_eq_false'])
        self.assertTrue(app.state['test_ne_true'])
        self.assertFalse(app.state['test_ne_false'])
        
        # Test ordering
        self.assertTrue(app.state['test_lt_true'])
        self.assertFalse(app.state['test_lt_false'])
        self.assertTrue(app.state['test_le_true'])
        self.assertFalse(app.state['test_le_false'])
        self.assertTrue(app.state['test_gt_true'])
        self.assertFalse(app.state['test_gt_false'])
        self.assertTrue(app.state['test_ge_true'])
        self.assertFalse(app.state['test_ge_false'])

    def test_time_functions(self):
        """Test datetime and time-related functions"""
        app = lingo_app(self.functions_spec)
        doc = render_output(app)
        
        # Find the datetime output in the rendered document
        datetime_found = False
        weekday_found = False
        random_found = False

        for n, element in enumerate(doc):
            if 'text' in element:
                text = element['text']
                # Check for datetime output (should be a datetime object converted to string)
                if 'datetime.now()' in text:
                    datetime_found = True
                elif 'current.weekday()' in text:
                    weekday_found = True
                elif 'random.randint(1, 10)' in text:
                    random_found = True
                elif text.isdigit() and 'weekday()' in str(doc[n - 1]):
                    # Weekday should be 0-6
                    weekday_val = int(text)
                    self.assertGreaterEqual(weekday_val, 0)
                    self.assertLessEqual(weekday_val, 6)
                elif text.isdigit() and 'weekday()' in str(doc[n - 1]):
                    # Weekday should be 0-6
                    weekday_val = int(text)
                    self.assertGreaterEqual(weekday_val, 0)
                    self.assertLessEqual(weekday_val, 6)
                elif text.isdigit() and 'randint(1, 10)' in str(doc[n - 1]):
                    # Random number should be 1-10
                    random_val = int(text)
                    self.assertGreaterEqual(random_val, 1)
                    self.assertLessEqual(random_val, 10)
        
        self.assertTrue(datetime_found, "Should find datetime.now() output")
        self.assertTrue(weekday_found, "Should find current.weekday() output")
        self.assertTrue(random_found, "Should find random.randint() output")

    
built_in = builtin_spec_files()
lingo_scripts = built_in['lingo_script']
lingo_script_test_data = built_in['lingo_script_test_data']

class TestLingoScripts(unittest.TestCase):

    def test_lingo_scripts(self):
        for name in lingo_scripts:
            with self.subTest(name=name):
                lingo_script = load_lingo_script_spec(name)
                test_data = load_lingo_script_spec(name.replace('.json', '_test_data.json'))

                default_app = lingo_app(lingo_script)
                default_result = lingo_execute(default_app, lingo_script['output'])

                self.assertEqual(default_result, test_data['results']['default'])

                for test_case in test_data['results']['test_cases']:
                    test_case_app = lingo_app(lingo_script, **test_case['params'])
                    result = lingo_execute(test_case_app, lingo_script['output'])

                    self.assertEqual(result, test_case['result'])

if __name__ == '__main__':
    unittest.main()
