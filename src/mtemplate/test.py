import unittest
import subprocess

from pathlib import Path
from mspec.core import load_generator_spec

class TestMTemplateApp(unittest.TestCase):

    spec: dict
    cmd: list[str]
    host: str | None

    def test_help_menus(self):

        # global help #

        for cmd in ['help', '--help', '-h']:
            global_help_cmd = self.cmd + [cmd]
            result = subprocess.run(global_help_cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('Displays this global help information.', result.stdout)

        # module help #

        for cmd in ['help', '--help', '-h']:
            module_help_cmd = self.cmd + ['template-module', cmd]
            result = subprocess.run(module_help_cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn(f'TemplateModule Help', result.stdout)

        # model help #

        for cmd in ['help', '--help', '-h']:
            model_help_cmd = self.cmd + ['template-module', 'single-model', cmd]
            result = subprocess.run(model_help_cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn(f'SingleModel Help', result.stdout)


    def test_bad_commands(self):
        pass

    def test_server_api(self):
        try:
            client_host = self.spec['client']['default_host'] if self.host is None else self.host
        except KeyError:
            raise ValueError('No default_host found in spec and no host provided for testing')

    def test_cli_db_commands(self):
        self.assertIsInstance(self.spec, dict)
        self.assertIsInstance(self.cmd, list)
        self.assertGreaterEqual(len(self.cmd), 0)

    def test_cli_http_commands(self):
        self.assertIsInstance(self.spec, dict)
        self.assertIsInstance(self.cmd, list)
        self.assertGreaterEqual(len(self.cmd), 0)


def test_spec(spec_path:str|Path, cli_args:list[str], host:str|None) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings (can be empty list)')

    test_suite = unittest.TestSuite()
    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host

    tests = unittest.TestLoader().loadTestsFromTestCase(TestMTemplateApp)
    test_suite.addTests(tests)

    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)

    return result.wasSuccessful()
