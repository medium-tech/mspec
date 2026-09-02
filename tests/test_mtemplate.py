import json
import subprocess
import unittest

from pathlib import Path

from mtemplate.core import MTemplateExtractor


sample_dir = Path(__file__).parent.parent / 'templates/tests'


class TestMTester(unittest.TestCase):

    #
    # cli tests
    #

    def _call_mtemplate_render(self, template_name:str, variables:dict) -> subprocess.CompletedProcess:
        args = [
            'python', '-m', 'mtemplate', 'render', 
            '-s', 'templates/tests/', 
            '-t', template_name, 
            '--vars', json.dumps(variables)
        ]
        return subprocess.run(args, capture_output=True, text=True)

    def _process_err(self, result:subprocess.CompletedProcess) -> str:
        return f'code: {result.returncode}; output: {result.stdout + result.stderr}'

    def test_cli_missing_template_variable(self):
        template_name = 'test_hello_world.py'

        result = self._call_mtemplate_render(template_name, {})
        self.assertEqual(result.returncode, 1, self._process_err(result))
        self.assertIn("'user_name' is undefined", result.stderr)
    
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
    # api tests
    #

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