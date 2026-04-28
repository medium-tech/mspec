import unittest
import datetime
import json
import sqlite3

from pprint import pprint

from mapp.context import MappContext, DBContext, ClientContext
from mapp.errors import MappValidationError
from mapp.types import new_model_class
from mapp.module.model.db import db_model_create_table, db_model_create, db_model_unique_counts, db_model_query

from mspec.core import load_browser2_spec, SAMPLE_BROWSER2_SPEC_DIR, builtin_spec_files, load_lingo_script_spec, SAMPLE_LINGO_SCRIPT_SPEC_DIR
from mspec.lingo import *


class TestLingoPages(unittest.TestCase):
    """
    Testing for browser2 page spec
    - test-page.json - tests that the calculated buffer is as expected for various inputs, etc
    - functions.json - tests that all functions in lingo_function_lookup are working as expected and that all are covered by tests
    """
        
    @classmethod
    def setUpClass(cls):
        cls.test_spec_path = SAMPLE_BROWSER2_SPEC_DIR / 'test-page.json'

        with open(cls.test_spec_path, 'r') as f:
            cls.test_spec = json.load(f)

        cls.function_files = [
            'functions-comparison',
            'functions-bool',
            'functions-int',
            'functions-float',
            'functions-str',
            'functions-struct',
            'functions-math',
            'functions-sequence',
            'functions-sequence-ops',
            'functions-datetime',
            'functions-random',
        ]
        cls.function_specs = []
        for name in cls.function_files:
            path = SAMPLE_BROWSER2_SPEC_DIR / f'{name}.json'
            with open(path, 'r') as f:
                attr = name.replace('-', '_')
                setattr(cls, f'{attr}_spec', json.load(f))
                cls.function_specs.append(getattr(cls, f'{attr}_spec'))

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

    def test_return_types(self):
        spec = load_browser2_spec('return-types.json')
        app = lingo_app(spec)
        doc = render_output(lingo_update_state(app))

    def test_all_functions_coverage(self):
        """Verify that all functions in lingo_function_lookup are tested"""
        
        # Get all function names from lingo_function_lookup
        expected_functions = set()
        for key, value in lingo_function_lookup.items():
            if isinstance(value, dict) and 'func' in value:
                expected_functions.add(key)
            elif isinstance(value, dict):
                # Nested functions like current.weekday, datetime.now, random.randint
                if key in ['auth', 'file_system', 'media', 'db']:
                    continue  # Skip built-in functions which have coverage elsewhere
                for subkey in value.keys():
                    expected_functions.add(f"{key}.{subkey}")
        
        # Check that we have state variables or direct calls for each function
        tested_functions = set()
        
        # Check state calculations for tested functions
        for func_spec in self.function_specs:
            for state_key, state_def in func_spec['state'].items():
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

        for func_spec in self.function_specs:
            for output_element in func_spec['output']:
                check_calls_in_element(output_element)
        
        # Verify coverage
        missing_functions = expected_functions - tested_functions
        self.assertEqual(len(missing_functions), 0, 
                        f"Missing tests for functions: {missing_functions}")

    def test_comparison_functions(self):
        """Test comparison operators: eq, ne, lt, le, gt, ge"""
        app = lingo_app(self.functions_comparison_spec)
        
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

    def test_bool_functions(self):
        """Test bool operators: bool, not, and, or"""
        app = lingo_app(self.functions_bool_spec)
        
        # Test bool function
        self.assertTrue(app.state['test_bool_true'])
        self.assertFalse(app.state['test_bool_false'])
        
        # Test not function
        self.assertFalse(app.state['test_not_true'])
        self.assertTrue(app.state['test_not_false'])
        
        # Test and function
        self.assertTrue(app.state['test_and_true'])
        self.assertFalse(app.state['test_and_false'])
        
        # Test or function
        self.assertTrue(app.state['test_or_true'])
        self.assertFalse(app.state['test_or_false'])

    def test_int_functions(self):
        """Test int conversion and negation functions: int, neg"""
        app = lingo_app(self.functions_int_spec)
        
        # Test neg function
        self.assertEqual(app.state['test_neg'], -5)
        
        # Test int function with number
        self.assertEqual(app.state['test_int'], 42)
        
        # Test int function with string and base
        self.assertEqual(app.state['test_int_base'], 42)

    def test_float_functions(self):
        """Test float conversion and rounding functions: float, round"""
        app = lingo_app(self.functions_float_spec)

        # Test float function
        self.assertEqual(app.state['test_float'], 0.001)

        # Test round function
        self.assertEqual(app.state['test_round_default'], 3)
        self.assertEqual(app.state['test_round_ndigits'], 3.142)

    def test_str_functions(self):
        """Test string functions: str, join"""
        app = lingo_app(self.functions_str_spec)
        
        # Test str function
        self.assertEqual(app.state['test_str'], '123')
        
        # Test join function
        self.assertEqual(app.state['test_join'], 'a-b-c')

    def test_struct_functions(self):
        """Test struct functions: key"""
        app = lingo_app(self.functions_struct_spec)

        # Test key function
        self.assertEqual(app.state['key_x_bool'], True)
        self.assertEqual(app.state['key_x_int'], 42)
        self.assertAlmostEqual(app.state['key_x_float'], 3.14)
        self.assertEqual(app.state['key_x_str'], 'hello.world')
        
    def test_math_functions(self):
        """Test math operators: add, sub, mul, div, floordiv, mod, pow, min, max, abs"""
        app = lingo_app(self.functions_math_spec)
        
        # Test arithmetic operations
        self.assertEqual(app.state['test_add'], 15)
        self.assertEqual(app.state['test_sub'], 7)
        self.assertEqual(app.state['test_mul'], 28)
        self.assertEqual(app.state['test_div'], 5.0)
        self.assertEqual(app.state['test_floordiv'], 7)
        self.assertEqual(app.state['test_mod'], 3)
        self.assertEqual(app.state['test_pow'], 8)
        
        # Test min/max/abs
        self.assertEqual(app.state['test_min'], 3)
        self.assertEqual(app.state['test_max'], 7)
        self.assertEqual(app.state['test_abs'], 10)

    def test_sequence_functions(self):
        """Test sequence functions: len, range, slice, any, all, sum, sorted"""
        app = lingo_app(self.functions_sequence_spec)

        # Test len
        self.assertEqual(app.state['test_len_list'], 5)
        self.assertEqual(app.state['test_len_string'], 5)
        
        # Test any and all
        self.assertTrue(app.state['test_any_true'])
        self.assertFalse(app.state['test_any_false'])
        self.assertTrue(app.state['test_all_true'])
        self.assertFalse(app.state['test_all_false'])

        # Test slice
        self.assertEqual(app.state['test_slice_default'], [0, 1])
        self.assertEqual(app.state['test_slice_start'], [2, 3, 4])
        self.assertEqual(app.state['test_slice_step'], [1, 3])
        
        # Test range
        self.assertEqual(app.state['test_range_default'], [0, 1, 2, 3, 4])
        self.assertEqual(app.state['test_range_start'], [1, 2, 3, 4, 5, 6])
        self.assertEqual(app.state['test_range_step'], [0, 2, 4, 6, 8])

        # Test sum and sorted
        self.assertEqual(app.state['test_sum'], 6)
        self.assertEqual(app.state['test_sum_start'], 16)
        self.assertEqual(app.state['test_sorted'], [2, 5, 9])
        self.assertEqual(app.state['test_sorted_strings'], ['apple', 'banana', 'cherry'])

    def test_sequence_ops_functions(self):
        """Test sequence ops: map, filter, dropwhile, takewhile, reversed, accumulate, reduce"""
        app = lingo_app(self.functions_sequence_ops_spec)

        # Test map
        self.assertEqual(app.state['test_map'], [11, 12, 13, 14, 15])

        # Test filter
        self.assertEqual(app.state['test_filter'], [4, 5, 6, 7])
        
        # Test dropwhile and takewhile
        self.assertEqual(app.state['test_dropwhile'], [4, 5, 6, 7])
        self.assertEqual(app.state['test_takewhile'], [1, 2, 3])
        
        # Test reversed
        self.assertEqual(app.state['test_reversed'], [3, 2, 1])

        # Test accumulate and reduce
        self.assertEqual(app.state['test_accumulate'], [1, 3, 6, 10])
        self.assertEqual(app.state['test_accumulate_initial'], [10, 11, 13, 16, 20])
        self.assertEqual(app.state['test_reduce'], 10)
        self.assertEqual(app.state['test_reduce_initial'], 20)

    def test_datetime_functions(self):
        """Test date and time functions: current.weekday, datetime.now"""
        app = lingo_app(self.functions_datetime_spec)
        doc = render_output(app)
        
        # Find the datetime output in the rendered document
        datetime_found = False
        weekday_found = False

        for n, element in enumerate(doc):
            if 'text' in element:
                text = element['text']
                # Check for datetime output (should be a datetime object converted to string)
                if 'datetime.now()' in text:
                    datetime_found = True
                elif 'current.weekday()' in text:
                    weekday_found = True
                elif text.isdigit() and 'weekday()' in str(doc[n - 1]):
                    # Weekday should be 0-6
                    weekday_val = int(text)
                    self.assertGreaterEqual(weekday_val, 0)
                    self.assertLessEqual(weekday_val, 6)
        
        self.assertTrue(datetime_found, "Should find datetime.now() output")
        self.assertTrue(weekday_found, "Should find current.weekday() output")

    def test_random_functions(self):
        """Test random functions: random.randint"""
        app = lingo_app(self.functions_random_spec)
        doc = render_output(app)
        
        # Find the random output in the rendered document
        random_found = False

        for n, element in enumerate(doc):
            if 'text' in element:
                text = element['text']
                if 'random.randint(1, 10)' in text:
                    random_found = True
                elif text.isdigit() and n > 0 and 'randint(1, 10)' in str(doc[n - 1]):
                    # Random number should be 1-10
                    random_val = int(text)
                    self.assertGreaterEqual(random_val, 1)
                    self.assertLessEqual(random_val, 10)
        
        self.assertTrue(random_found, "Should find random.randint() output")

    def test_structs_page(self):
        """Test struct rendering functionality with all supported types"""
        spec = load_browser2_spec('structs.json')
        app = lingo_app(spec)
        doc = render_output(lingo_update_state(app))
        
        # Verify we have the expected number of elements
        self.assertEqual(len(doc), 50, f'Should have 50 output elements, got {len(doc)}')
        
        # Verify main heading
        self.assertEqual(doc[0]['heading'], 'Individual Structs')
        self.assertEqual(doc[0]['level'], 1)
        
        # Test primitives: str, int, bool #
        
        # Hardcoded primitive struct
        self.assertEqual(doc[3]['type'], 'struct')
        self.assertEqual(doc[3]['value']['color'], 'red')
        self.assertEqual(doc[3]['value']['amount'], 10)
        self.assertEqual(doc[3]['value']['in_stock'], True)
        
        # Typed primitive struct
        self.assertEqual(doc[6]['type'], 'struct')
        self.assertEqual(doc[6]['value']['color']['type'], 'str')
        self.assertEqual(doc[6]['value']['color']['value'], 'green')
        self.assertEqual(doc[6]['value']['amount']['type'], 'int')
        self.assertEqual(doc[6]['value']['amount']['value'], 20)
        self.assertEqual(doc[6]['value']['in_stock']['type'], 'bool')
        self.assertEqual(doc[6]['value']['in_stock']['value'], True)
        
        # Dynamic primitive struct
        self.assertEqual(doc[9]['type'], 'struct')
        self.assertEqual(doc[9]['display']['headers'], False)
        self.assertEqual(doc[9]['value']['color'], {'value': 'blue', 'type': 'str'})
        self.assertEqual(doc[9]['value']['amount'], {'value': 20, 'type': 'int'})
        self.assertEqual(doc[9]['value']['in_stock'], {'value': True, 'type': 'bool'})
        
        # Test primitives: float, datetime #
        
        # Hardcoded float/datetime struct
        self.assertEqual(doc[12]['type'], 'struct')
        self.assertAlmostEqual(doc[12]['value']['price'], 19.99)
        self.assertAlmostEqual(doc[12]['value']['weight'], 2.5)
        self.assertEqual(doc[12]['value']['created_at'], '2024-01-15T10:30:00')
        self.assertEqual(doc[12]['value']['updated_at'], '2024-06-20T14:45:30')
        
        # Typed float/datetime struct
        self.assertEqual(doc[15]['type'], 'struct')
        self.assertEqual(doc[15]['value']['price']['type'], 'float')
        self.assertAlmostEqual(doc[15]['value']['price']['value'], 29.99)
        self.assertEqual(doc[15]['value']['weight']['type'], 'float')
        self.assertAlmostEqual(doc[15]['value']['weight']['value'], 3.75)
        self.assertEqual(doc[15]['value']['created_at']['type'], 'datetime')
        self.assertEqual(doc[15]['value']['created_at']['value'], '2023-12-01T08:00:00')
        
        # Dynamic float struct
        self.assertEqual(doc[18]['type'], 'struct')
        self.assertAlmostEqual(doc[18]['value']['price']['value'], 19.99)
        self.assertAlmostEqual(doc[18]['value']['weight']['value'], 2.5)
        
        # Test lists of primitives #
        
        # Hardcoded lists
        self.assertEqual(doc[21]['type'], 'struct')
        self.assertEqual(doc[21]['value']['tags'], ['urgent', 'important', 'review'])
        self.assertEqual(doc[21]['value']['scores'], [85, 92, 78, 95])
        self.assertAlmostEqual(doc[21]['value']['measurements'][0], 3.14, places=2)
        
        # Typed lists
        self.assertEqual(doc[24]['type'], 'struct')
        self.assertEqual(doc[24]['value']['tags']['type'], 'list')
        self.assertEqual(doc[24]['value']['tags']['value'], ['electronics', 'gadgets', 'tech'])
        self.assertEqual(doc[24]['value']['scores']['type'], 'list')
        self.assertEqual(doc[24]['value']['scores']['value'], [88, 91, 79])
        self.assertEqual(doc[24]['value']['flags']['type'], 'list')
        self.assertEqual(doc[24]['value']['flags']['value'], [True, False, True, True])
        
        # Dynamic lists
        self.assertEqual(doc[27]['type'], 'struct')
        self.assertEqual(doc[27]['value']['tags']['value'], ['1', '2', '3'])
        self.assertEqual(doc[27]['value']['total_score'], {'value': 60, 'type': 'int'})
        
        # Test datetime lists #
        
        # Hardcoded datetime lists
        self.assertEqual(doc[30]['type'], 'struct')
        self.assertIn('event_dates', doc[30]['value'])
        self.assertIsInstance(doc[30]['value']['event_dates'], list)
        
        # Typed datetime lists
        self.assertEqual(doc[33]['type'], 'struct')
        self.assertEqual(doc[33]['value']['event_dates']['type'], 'list')
        
        # Test mixed struct with all types #
        self.assertEqual(doc[36]['type'], 'struct')
        self.assertEqual(doc[36]['value']['name'], 'Product A')
        self.assertEqual(doc[36]['value']['quantity'], 42)
        self.assertEqual(doc[36]['value']['in_stock'], True)
        self.assertAlmostEqual(doc[36]['value']['price'], 99.95)
        self.assertEqual(doc[36]['value']['launch_date'], '2024-01-15T10:00:00')
        
        # Verify list of structs heading
        self.assertEqual(doc[37]['heading'], 'List of Structs')
        self.assertEqual(doc[37]['level'], 1)
        
        # Test basic types table #
        self.assertEqual(doc[40]['type'], 'list')
        self.assertEqual(doc[40]['display']['format'], 'table')
        self.assertEqual(len(doc[40]['display']['headers']), 3)
        self.assertEqual(len(doc[40]['value']), 3)
        
        # Verify all items in basic table are structs
        for item in doc[40]['value']:
            self.assertEqual(item['type'], 'struct')
            self.assertIn('value', item)
        
        # Test float and datetime table #
        self.assertEqual(doc[43]['type'], 'list')
        self.assertEqual(doc[43]['display']['format'], 'table')
        headers = doc[43]['display']['headers']
        self.assertEqual(headers[0]['field'], 'product')
        self.assertEqual(headers[1]['field'], 'price')
        self.assertEqual(headers[2]['field'], 'weight')
        self.assertEqual(headers[3]['field'], 'date_added')
        
        # Test lists as field values table #
        self.assertEqual(doc[46]['type'], 'list')
        self.assertEqual(doc[46]['display']['format'], 'table')
        headers = doc[46]['display']['headers']
        self.assertEqual(headers[1]['field'], 'tags')
        self.assertEqual(headers[2]['field'], 'scores')
        self.assertEqual(headers[3]['field'], 'flags')
        
        # Verify struct with list fields has appropriate values
        first_item = doc[46]['value'][0]
        self.assertEqual(first_item['type'], 'struct')
        self.assertIsInstance(first_item['value']['tags'], list)
        self.assertIsInstance(first_item['value']['scores'], list)
        self.assertIsInstance(first_item['value']['flags'], list)

    
built_in = builtin_spec_files()
lingo_scripts = built_in['lingo_script']
lingo_script_test_data = built_in['lingo_script_test_data']

class TestLingoScripts(unittest.TestCase):
    """
    Tests all lingo scripts against their test data/cases
    """

    def test_lingo_scripts(self):
        for name in lingo_scripts:
            with self.subTest(name=name):
                lingo_script = load_lingo_script_spec(name)
                test_data_path = SAMPLE_LINGO_SCRIPT_SPEC_DIR / name.replace('.json', '_test_data.json')
                with open(test_data_path) as f:
                    test_data = json.load(f)

                default_app = lingo_app(lingo_script)
                default_result = lingo_execute(default_app, lingo_script['output'])

                self.assertEqual(default_result, test_data['results']['default'])

                for test_case in test_data['results']['test_cases']:
                    test_case_app = lingo_app(lingo_script, **test_case['params'])
                    result = lingo_execute(test_case_app, lingo_script['output'])

                    self.assertEqual(result, test_case['result'])


def _in_mem_sql_text_ctx():
    conn = sqlite3.connect(':memory:')
    db = DBContext(db_url=':memory:', connection=conn, cursor=conn.cursor(), commit=conn.commit)
    return MappContext(
        server_port=8000,
        client=ClientContext(host='http://localhost:8000', headers={}),
        db=db,
        log=lambda msg: None,
    )


def _make_post_spec():
    return {
        'name': {'lower_case': 'post', 'snake_case': 'post', 'pascal_case': 'Post', 'kebab_case': 'post'},
        'auth': {'require_login': False, 'max_models_per_user': -1},
        'fields': {
            'user_id': {
                'name': {'lower_case': 'user id', 'snake_case': 'user_id'},
                'type': 'foreign_key',
                'references': {'module': 'auth', 'table': 'user', 'field': 'id'},
            },
            'title': {
                'name': {'lower_case': 'title', 'snake_case': 'title'},
                'type': 'str',
            },
            'view_count': {
                'name': {'lower_case': 'view count', 'snake_case': 'view_count'},
                'type': 'int',
            },
        },
        'non_list_fields': [
            {'name': {'lower_case': 'user id', 'snake_case': 'user_id'}, 'type': 'foreign_key', 'references': {'module': 'auth', 'table': 'user', 'field': 'id'}},
            {'name': {'lower_case': 'title', 'snake_case': 'title'}, 'type': 'str'},
            {'name': {'lower_case': 'view count', 'snake_case': 'view_count'}, 'type': 'int'},
        ],
        'list_fields': [],
    }


def _make_reaction_spec():
    return {
        'name': {'lower_case': 'reaction', 'snake_case': 'reaction', 'pascal_case': 'Reaction', 'kebab_case': 'reaction'},
        'auth': {'require_login': False, 'max_models_per_user': -1},
        'fields': {
            'post_id': {
                'name': {'lower_case': 'post id', 'snake_case': 'post_id'},
                'type': 'foreign_key',
                'references': {'module': 'app', 'table': 'post', 'field': 'id'},
            },
            'reaction_type': {
                'name': {'lower_case': 'reaction type', 'snake_case': 'reaction_type'},
                'type': 'str',
            },
        },
        'non_list_fields': [
            {'name': {'lower_case': 'post id', 'snake_case': 'post_id'}, 'type': 'foreign_key', 'references': {'module': 'app', 'table': 'post', 'field': 'id'}},
            {'name': {'lower_case': 'reaction type', 'snake_case': 'reaction_type'}, 'type': 'str'},
        ],
        'list_fields': [],
    }


def _make_module_spec(models_dict):
    return {
        'name': {'lower_case': 'test app', 'snake_case': 'test_app', 'pascal_case': 'TestApp', 'kebab_case': 'test-app'},
        'models': models_dict,
    }


class TestLingoDbFunctions(unittest.TestCase):
    """Tests for db.create, db.read, db.unique_counts, and db.query lingo functions"""

    @classmethod
    def setUpClass(cls):
        post_spec = _make_post_spec()
        reaction_spec = _make_reaction_spec()

        module_spec = _make_module_spec({'post': post_spec, 'reaction': reaction_spec})

        cls.post_class = new_model_class(post_spec, module_spec)
        cls.reaction_class = new_model_class(reaction_spec, module_spec)
        cls.module_spec = module_spec

        cls.lingo_spec = {
            'params': {},
            'state': {},
            'modules': {'test_app': module_spec},
        }

    def setUp(self):
        self.ctx = _in_mem_sql_text_ctx()
        db_model_create_table(self.ctx, self.post_class)
        db_model_create_table(self.ctx, self.reaction_class)

        post1 = self.post_class(id=None, user_id='1', title='hello', view_count=10)
        post2 = self.post_class(id=None, user_id='2', title='world', view_count=20)
        db_model_create(self.ctx, self.post_class, post1)
        db_model_create(self.ctx, self.post_class, post2)

        r1 = self.reaction_class(id=None, post_id='1', reaction_type='like')
        r2 = self.reaction_class(id=None, post_id='1', reaction_type='like')
        r3 = self.reaction_class(id=None, post_id='1', reaction_type='love')
        db_model_create(self.ctx, self.reaction_class, r1)
        db_model_create(self.ctx, self.reaction_class, r2)
        db_model_create(self.ctx, self.reaction_class, r3)

    def tearDown(self):
        self.ctx.db.connection.close()

    def _make_app(self):
        return LingoApp(spec=self.lingo_spec, params={}, state={}, buffer=[])

    # db.create tests #

    def test_db_create_returns_new_id_string(self):
        expression = {
            'call': 'db.create',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'data': {
                    'type': 'struct',
                    'value': {
						'user_id': {'value': '3', 'type': 'str'},
						'title': {'value': 'new post', 'type': 'str'},
						'view_count': {'value': 30, 'type': 'int'},
					}
				},
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['type'], 'str')
        self.assertIsInstance(result['value'], str)
        self.assertTrue(result['value'])

        read_result = lingo_execute(app, {
            'call': 'db.read',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'model_id': {'value': result['value'], 'type': 'str'},
            }
        }, self.ctx)
        self.assertEqual(read_result['value']['title'], 'new post')
        self.assertEqual(read_result['value']['view_count'], 30)
        self.assertEqual(read_result['value']['user_id'], '3')
        
    def test_db_create_with_primitive_struct(self):
        expression = {
            'call': 'db.create',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'data': {
                    'user_id': '3',
                    'title': 'new post',
                    'view_count': 30,
                },
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['type'], 'str')
        self.assertIsInstance(result['value'], str)
        self.assertTrue(result['value'])

        read_result = lingo_execute(app, {
            'call': 'db.read',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'model_id': {'value': result['value'], 'type': 'str'},
            }
        }, self.ctx)
        self.assertEqual(read_result['value']['title'], 'new post')
        self.assertEqual(read_result['value']['view_count'], 30)
        self.assertEqual(read_result['value']['user_id'], '3')

    def test_db_create_validates_data(self):
        expression = {
            'call': 'db.create',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'data': {
                    'user_id': {'value': '4', 'type': 'str'},
                    'title': {'value': 'bad post', 'type': 'str'},
                    'view_count': {'value': 'not an int', 'type': 'str'},
                },
            }
        }
        app = self._make_app()
        with self.assertRaises(MappValidationError):
            lingo_execute(app, expression, self.ctx)

    # db.read tests #

    def test_db_read_returns_struct(self):
        expression = {
            'call': 'db.read',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'model_id': {'value': '1', 'type': 'str'},
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['type'], 'struct')
        self.assertEqual(result['value']['id'], '1')
        self.assertEqual(result['value']['title'], 'hello')
        self.assertEqual(result['value']['view_count'], 10)

    def test_db_read_returns_correct_fields(self):
        expression = {
            'call': 'db.read',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'model_id': {'value': '2', 'type': 'str'},
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['value']['title'], 'world')
        self.assertEqual(result['value']['user_id'], '2')
        self.assertEqual(result['value']['view_count'], 20)

    # db.unique_counts tests #

    def test_db_unique_counts_returns_list(self):
        expression = {
            'call': 'db.unique_counts',
            'args': {
                'model_type': {'value': 'test_app.reaction', 'type': 'str'},
                'group_by': {'value': 'reaction_type', 'type': 'str'},
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['type'], 'list')
        self.assertEqual(len(result['value']), 2)
        counts = {item['value']['group']: item['value']['count'] for item in result['value']}
        self.assertEqual(counts['like'], 2)
        self.assertEqual(counts['love'], 1)

    def test_db_unique_counts_with_filter(self):
        expression = {
            'call': 'db.unique_counts',
            'args': {
                'model_type': {'value': 'test_app.reaction', 'type': 'str'},
                'group_by': {'value': 'reaction_type', 'type': 'str'},
                'filters': {
                    'type': 'struct',
                    'value': {'post_id': {'value': '1', 'type': 'str'}},
                },
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertEqual(result['type'], 'list')
        counts = {item['value']['group']: item['value']['count'] for item in result['value']}
        self.assertEqual(counts['like'], 2)
        self.assertEqual(counts['love'], 1)

    # db.query tests #

    def test_db_query_returns_matching_str_field(self):
        expression = {
            'call': 'db.query',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'where': {
                    'type': 'struct',
                    'value': {
                        'title': {
                            'eq': 'hello'
                        }
                    }
                },
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'struct')
        self.assertIsInstance(result['value'], dict)
        self.assertIsInstance(result['value'].get('items'), list)
        self.assertIsInstance(result['value'].get('total'), int)
        self.assertEqual(result['value']['total'], 1)
        self.assertEqual(len(result['value']['items']), 1)
        first_item = result['value']['items'][0]
        self.assertEqual(first_item['id'], '1')
        self.assertEqual(first_item['user_id'], '1')
        self.assertEqual(first_item['title'], 'hello')
        self.assertEqual(first_item['view_count'], 10)

    def test_db_query_returns_matching_foreign_key_field(self):
        expression = {
            'call': 'db.query',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'where': {
                    'type': 'struct',
                    'value': {
                        'user_id': {
                            'eq': '2'
                        }
                    }
                }
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['value'].get('items'), list)
        self.assertIsInstance(result['value'].get('total'), int)
        self.assertEqual(result['value']['total'], 1)
        self.assertEqual(result['value']['items'][0]['user_id'], '2')

    def test_db_query_returns_empty_list_when_no_match(self):
        expression = {
            'call': 'db.query',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'where': {
                    'title': {
                        'eq': 'nonexistent'
                    }
                },
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['value'].get('total'), int)
        self.assertEqual(result['value']['total'], 0)
        self.assertEqual(result['value']['items'], [])

    def test_db_query_returns_multiple_matching_rows(self):
        # Add a second post for user_id '1'
        extra = self.post_class(id=None, user_id='1', title='another post', view_count=5)
        db_model_create(self.ctx, self.post_class, extra)

        expression = {
            'call': 'db.query',
            'args': {
                'model_type': {'value': 'test_app.post', 'type': 'str'},
                'where': {
                    'user_id': {
                        'eq': {
                            'type': 'str',
                            'value': '1',
                        }
                    }
                }
            }
        }
        app = self._make_app()
        result = lingo_execute(app, expression, self.ctx)
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result['value'].get('items'), list)
        self.assertIsInstance(result['value'].get('total'), int)
        self.assertEqual(result['value']['total'], 2)
        titles = {item['title'] for item in result['value']['items']}
        self.assertEqual(titles, {'hello', 'another post'})

    def test_db_query_raises_on_unsupported_field_type(self):
        with self.assertRaises(ValueError) as cm:
            db_model_query(self.ctx, self.post_class, {'view_count': 10})
        self.assertIn('unsupported field type', str(cm.exception))


if __name__ == '__main__':
    unittest.main()
