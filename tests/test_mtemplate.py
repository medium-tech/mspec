import json
import shutil
import subprocess
import unittest

from pathlib import Path

from jinja2 import TemplateError

from mtemplate.core import MTemplateExtractor, apply_template_slots


sample_dir = Path(__file__).parent.parent / 'templates/tests'
tmp_dir = Path(__file__).parent / 'tmp'


class TestMTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        shutil.rmtree(tmp_dir)

    def _mk_tmp_dir(self, name:str) -> Path:
        output_dir = tmp_dir / name
        output_dir.mkdir(parents=True, exist_ok=False)
        return output_dir

    def _call_mtemplate_render(self, template_name:str, variables:dict, debug:bool=False, disable_strict:bool=False, output:str=None) -> subprocess.CompletedProcess:
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
        if output is not None:
            args += ['-o', output]
        return subprocess.run(args, capture_output=True, text=True)

    def _call_mtemplate_slots(self, child_source:Path, output:str=None) -> subprocess.CompletedProcess:
        args = [
            'python', '-m', 'mtemplate', 'slots', 
            '-s', str(child_source), 
        ]

        if output is not None:
            args += ['-o', output]
            
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

    def test_cli_test_print_output(self):
        template_name = 'test_hello_world.py'

        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, Alice.')")
    
    def test_cli_print_output_with_debug(self):
        template_name = 'test_hello_world.py'

        # debug mode prints the raw jinja template, undefined vars are not needed
        result = self._call_mtemplate_render(template_name, {}, debug=True)
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, {{ user_name }}.')")

        # without debug mode, the same template renders normally and requires vars
        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, Alice.')")

    def test_cli_write_output(self):
        template_name = 'test_hello_world.py'

        output_dir = self._mk_tmp_dir('test_cli_write_output')
        output_path = output_dir / 'output.py'
        self.assertFalse(output_path.exists())

        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'}, output=str(output_path))
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout, '')
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text().strip(), "print('Hello, Alice.')")

    def test_cli_write_output_with_debug(self):
        template_name = 'test_hello_world.py'

        output_dir = self._mk_tmp_dir('test_cli_write_output_with_debug')
        output_path = output_dir / 'output.py'
        debug_output_path = output_dir / 'output.py.jinja2'
        self.assertFalse(output_path.exists())
        self.assertFalse(debug_output_path.exists())

        result = self._call_mtemplate_render(template_name, {'user_name': 'Alice'}, debug=True, output=str(output_path))
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout, '')

        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text().strip(), "print('Hello, Alice.')")

        self.assertTrue(debug_output_path.exists())
        self.assertEqual(debug_output_path.read_text().strip(), "print('Hello, {{ user_name }}.')")

    def test_cli_slots(self):

        #
        # setup
        #

        output_dir = self._mk_tmp_dir('test_cli_slots')
        parent_path = output_dir / 'test_parent.py'
        child_path = output_dir / 'test_child.py'

        shutil.copy(sample_dir / 'test_parent.py', parent_path)
        shutil.copy(sample_dir / 'test_child.py', child_path)

        self.assertTrue(parent_path.exists())
        self.assertTrue(child_path.exists())

        orig_msg = 'i am the parent template'
        new_msg = 'i am a unittest for slots'

        orig_parent_text = parent_path.read_text()
        orig_child_text = child_path.read_text()

        self.assertIn(orig_msg, orig_parent_text)
        self.assertIn(orig_msg, orig_child_text)

        #
        # change parent text
        #

        with open(parent_path, 'w') as parent_src:
            parent_src.truncate()
            parent_src.write(orig_parent_text.replace(orig_msg, new_msg))

        #
        # render slots - print to stdout
        #

        result_1 = self._call_mtemplate_slots(child_path)

        expected_output = """# slot :: custom_imports
from typing import List
# end slot ::

print('i am a unittest for slots')

# slot :: custom_code
def custom_function():
    pass
# end slot ::

# parent :: ./test_parent.py"""

        self.assertEqual(result_1.returncode, 0)
        self.assertEqual(expected_output.strip(), result_1.stdout.strip())

        #
        # render slots - write to file
        #

        # confirm child template hasn't changed
        self.assertNotIn(new_msg, child_path.read_text())

        result_2 = self._call_mtemplate_slots(child_path, output=child_path)

        self.assertEqual(result_2.returncode, 0)

        self.assertNotIn(orig_msg, child_path.read_text())
        self.assertIn(new_msg, child_path.read_text())

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