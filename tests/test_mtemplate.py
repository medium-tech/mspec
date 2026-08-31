import json
import subprocess
import unittest


class TestMTester(unittest.TestCase):

    def _call_mtemplate_render(self, source:str, variables:dict) -> subprocess.CompletedProcess:
        args = ['python', '-m', 'mtemplate', 'render', '-s', source, '--vars', json.dumps(variables)]
        return subprocess.run(args, capture_output=True, text=True)

    def _process_err(self, result:subprocess.CompletedProcess) -> str:
        return f'code: {result.returncode}; output: {result.stdout + result.stderr}'

    def test_missing_template_variable(self):
        path = 'templates/tests/test_1.py'

        result = self._call_mtemplate_render(path, {})
        self.assertEqual(result.returncode, 1, self._process_err(result))
        self.assertIn("'user_name' is undefined", result.stderr)
    
    def test_test_1_file(self):
        path = 'templates/tests/test_1.py'

        result = self._call_mtemplate_render(path, {'user_name': 'Alice'})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Hello, Alice.')")

    def test_test_2_file(self):
        path = 'templates/tests/test_2.py'

        result = self._call_mtemplate_render(path, {'items': ['Alice', 'Bob']})
        self.assertEqual(result.returncode, 0, self._process_err(result))
        self.assertEqual(result.stdout.strip(), "print('Alice')\n\nprint('Bob')")