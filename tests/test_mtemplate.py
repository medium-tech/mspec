import json
import subprocess
import unittest

from pathlib import Path

from jinja2 import TemplateError

from mtemplate.core import MTemplateExtractor


sample_dir = Path(__file__).parent.parent / 'templates/tests'


class TestMTester(unittest.TestCase):

    def _call_mtemplate_render(self, template_name:str, variables:dict, debug:bool=False, disable_strict:bool=False) -> subprocess.CompletedProcess:
        args = [
            'python', '-m', 'mtemplate', 'render', 
            '-s', 'templates/tests/', 
            '-t', template_name, 
            '--vars', json.dumps(variables)
        ]
        if debug:
            args.append('--debug')
        if disable_strict:
            args.append('--disable-strict')
        return subprocess.run(args, capture_output=True, text=True)

    def _process_err(self, result:subprocess.CompletedProcess) -> str:
        return f'code: {result.returncode}; output: {result.stdout + result.stderr}'

    #
    # cli features
    #
    
    def test_cli_missing_template_variable(self):
        template_name = 'test_hello_world.py'

        result = self._call_mtemplate_render(template_name, {})
        self.assertEqual(result.returncode, 1, self._process_err(result))
        self.assertIn("'user_name' is undefined", result.stderr)

    def test_cli_disable_strict(self):
        template_name = 'test_hello_world.py'

        result = self._call_mtemplate_render(template_name, {}, disable_strict=True)
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertNotIn("'user_name' is undefined", result.stderr)
        self.assertEqual(result.stdout.strip(), "print('Hello, .')")

    def test_cli_debug_mode(self):
        template_name = 'test_hello_world.py'

        # debug mode prints the raw jinja template, undefined vars are not needed
        result = self._call_mtemplate_render(template_name, {}, debug=True)
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, {{ user_name }}.')")

        # without debug mode, the same template renders normally and requires vars
        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, Alice.')")

    #
    # cli test files
    #

    def test_cli_test_hello_world(self):
        template_name = 'test_hello_world.py'

        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, Alice.')")

    def test_cli_test_for(self):
        template_name = 'test_for.py'

        result = self._call_mtemplate_render(template_name, {'msgs': ['Hello', 'Goodbye'], 'names': ['Alice', 'Bob']})
        self.assertEqual(result.returncode, 0, self._process_err(result))

        expected_output = """
# say - hello
print('Hello Alice')
print('Hello Bob')

# say - goodbye
print('Goodbye Alice')
print('Goodbye Bob')
""".strip()

        self.assertEqual(result.stdout.strip(), expected_output)

    
    #
    # api features
    #

    def test_api_missing_template_variable(self):
        template = 'test_hello_world.py'
        extractor = MTemplateExtractor.init_from_dir(sample_dir)

        with self.assertRaises(TemplateError) as ctx:
            extractor.render_template(template, {})
        self.assertIn("'user_name' is undefined", str(ctx.exception))

    def test_api_disable_strict(self):
        template = 'test_hello_world.py'
        extractor = MTemplateExtractor.init_from_dir(sample_dir, disable_strict=True)

        rendered_template = extractor.render_template(template, {})
        self.assertEqual(rendered_template.strip(), "print('Hello, .')")

    def test_api_debug_mode(self):
        template = 'test_hello_world.py'

        # debug mode returns the raw jinja template, undefined vars are not needed
        debug_extractor = MTemplateExtractor.init_from_dir(sample_dir, debug=True)
        rendered_template = debug_extractor.render_template(template, {})
        self.assertEqual(rendered_template.strip(), "print('Hello, {{ user_name }}.')")

        # without debug mode, the same template renders normally and requires vars
        extractor = MTemplateExtractor.init_from_dir(sample_dir)
        rendered_template = extractor.render_template(template, {'user_name': 'Alice'})
        self.assertEqual(rendered_template.strip(), "print('Hello, Alice.')")

    #
    # api test files
    #

    def test_api_hello_world(self):
        template = 'test_hello_world.py'
        extractor = MTemplateExtractor.init_from_dir(sample_dir)

        rendered_template = extractor.render_template(template, {'user_name': 'Alice'})
        self.assertEqual(rendered_template.strip(), "print('Hello, Alice.')")

    def test_api_test_for(self):
        template = 'test_for.py'
        extractor = MTemplateExtractor.init_from_dir(sample_dir)

        rendered_template = extractor.render_template(template, {'msgs': ['Hello', 'Goodbye'], 'names': ['Alice', 'Bob']})

        expected_output = """
# say - hello
print('Hello Alice')
print('Hello Bob')

# say - goodbye
print('Goodbye Alice')
print('Goodbye Bob')
""".strip()

        self.assertEqual(rendered_template.strip(), expected_output)

    def test_api_branching(self):
        template = 'test_branching.py'
        extractor = MTemplateExtractor.init_from_dir(sample_dir)

        # case 1 #

        rendered_template = extractor.render_template(template, {'color': 'green', 'option': True})

        self.assertIn("print('Option Selected!')", rendered_template)
        self.assertIn("print('green')", rendered_template)

        # case 2 #

        rendered_template = extractor.render_template(template, {'color': 'other', 'option': False})

        self.assertNotIn("print('Option Selected!')", rendered_template)
        self.assertEqual(rendered_template.strip(), "print('unknown :(')")

    def test_api_macros(self):
        template = 'test_macros.py'
        
        # case 1 #

        extractor = MTemplateExtractor.init_from_dir(sample_dir)
        rendered_template = extractor.render_template(template, {'user_name': 'Charlie'})

        expected_output = """
print('Greetings Python!')

print('Greetings Charlie!')
""".strip()

        self.assertEqual(rendered_template.strip(), expected_output)