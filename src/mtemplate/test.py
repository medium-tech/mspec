import unittest

from pathlib import Path
from mspec.core import load_generator_spec

class TestMTemplateApp(unittest.TestCase):

    spec: dict
    cmd: list[str]

    def test_help_menus(self):
        pass

    def test_bad_commands(self):
        pass

    def test_cli_db_commands(self):
        self.assertIsInstance(self.spec, dict)
        self.assertIsInstance(self.cmd, list)
        self.assertGreaterEqual(len(self.cmd), 0)

    def test_cli_http_commands(self):
        self.assertIsInstance(self.spec, dict)
        self.assertIsInstance(self.cmd, list)
        self.assertGreaterEqual(len(self.cmd), 0)


def test_spec(spec_path:str|Path, cli_args:list[str]) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings (can be empty list)')

    test_suite = unittest.TestSuite()
    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args

    tests = unittest.TestLoader().loadTestsFromTestCase(TestMTemplateApp)
    test_suite.addTests(tests)

    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)

    return result.wasSuccessful()
