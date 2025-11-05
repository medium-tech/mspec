import unittest
import subprocess

from pathlib import Path
from mspec.core import load_generator_spec

class TestMTemplateApp(unittest.TestCase):

    """
    Test suite for the mtemplate app generation spec

    Generated App:
        While the applications have their own tests, this suite
        exits to ensure that the generated application matches the
        expected behavior as defined in the spec. This is necessary
        to validate the code generation process.

    Template Apps:
        This test suite is also used to validate the template apps
        themselves. (Currently just mspec/templates/go)

    """

    spec: dict
    cmd: list[str]
    host: str | None

    def _run_cmd(self, cmd:list[str]) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f'exit {result.returncode} for command "{" ".join(cmd)}" output: {result.stdout + result.stderr}')
        return result

    def test_help_menus(self):

        # global help #

        for global_help_arg in ['help', '--help', '-h']:
            global_help_cmd = self.cmd + [global_help_arg]
            result = self._run_cmd(global_help_cmd)
            self.assertIn('Displays this global help information.', result.stdout)

        # module help #

        try:
            modules: dict = self.spec['modules']
        except KeyError:
            raise ValueError('No modules found in spec for help menu testing')

        for module in modules.values():
            for module_help_arg in ['help', '--help', '-h']:
                module_help_cmd = self.cmd + [module['name']['kebab_case'], module_help_arg]
                result = self._run_cmd(module_help_cmd)
                self.assertIn(f'{module["name"]["pascal_case"]} Help', result.stdout)

            # each model in module help #

            for model in module.get('models', {}).values():
                for model_help_arg in ['help', '--help', '-h']:
                    model_help_cmd = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], model_help_arg]
                    result = self._run_cmd(model_help_cmd)
                    self.assertIn(f'{model["name"]["pascal_case"]} Help', result.stdout)


    def test_bad_commands(self):
        pass

    def test_server_api(self):
        try:
            client_host = self.spec['client']['default_host'] if self.host is None else self.host
        except KeyError:
            raise ValueError('No default_host found in spec and no host provided for testing')

    def test_cli_db_commands(self):
        pass

    def test_cli_http_commands(self):
        pass


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
