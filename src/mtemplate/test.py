import unittest
import json
import subprocess

from pathlib import Path
from mspec.core import load_generator_spec

def example_from_model(model:dict, index=0) -> dict:
    data = {}
    for field_name, field in model.get('fields', {}).items():
        try:
            value = field['examples'][index]
        except (IndexError, KeyError):
            raise ValueError(f'No example for field "{model["name"]["pascal_case"]}.{field_name}" at index {index}')
        
        data[field_name] = value

    return data

class TestMTemplateApp(unittest.TestCase):
    
    maxDiff = None

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

    def _run_cmd(self, cmd:list[str], expected_code=0) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True)
        msg = f'expected {expected_code} got {result.returncode} for command "{" ".join(cmd)}" output: {result.stdout + result.stderr}'
        self.assertEqual(result.returncode, expected_code, msg)
        return result

    def test_help_menus(self):

        # global help #

        for global_help_arg in ['help', '--help', '-h']:
            global_help_cmd = self.cmd + [global_help_arg]
            result = self._run_cmd(global_help_cmd)
            self.assertIn('Displays this global help information.', result.stdout)

        # module help #

        for module in self.spec['modules'].values():
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

    def _test_cli_crud_commands(self, command_type:str):
        for module in self.spec['modules'].values():
            for model_name, model in module['models'].items():
                model_db_args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], command_type]

                # create #

                example_to_create = example_from_model(model)
                result = self._run_cmd(model_db_args + ['create', json.dumps(example_to_create)])
                created_model = json.loads(result.stdout)

                created_model_id = created_model.pop('id')  # remove id for comparison
                self.assertEqual(created_model, example_to_create, f'Created {model_name} does not match example data')

                # read #

                result = self._run_cmd(model_db_args + ['read', str(created_model_id)])
                read_model = json.loads(result.stdout)
                read_model_id = read_model.pop('id')
                self.assertEqual(read_model, example_to_create, f'Read {model_name} does not match example data')
                self.assertEqual(read_model_id, created_model_id, f'Read {model_name} ID does not match created ID')

                # update #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                result = self._run_cmd(model_db_args + ['update', created_model_id, json.dumps(updated_example)])
                updated_model = json.loads(result.stdout)
                updated_model_id = updated_model.pop('id')
                self.assertEqual(updated_model, updated_example, f'Updated {model_name} does not match updated example data')
                self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} ID does not match created ID')

                # delete #

                result = self._run_cmd(model_db_args + ['delete', str(created_model_id)])
                delete_output = json.loads(result.stdout)
                self.assertEqual(delete_output['id'], created_model_id, f'Deleted {model_name} ID does not match created ID')
                self.assertEqual(delete_output['message'], f'deleted {model["name"]["lower_case"]} {created_model_id}')

                # read after delete #

                result = self._run_cmd(model_db_args + ['read', str(created_model_id)], expected_code=1)
                read_output = json.loads(result.stdout)
                self.assertEqual(read_output['code'], 'not_found', f'Read after delete for {model_name} did not return not_found code')
                self.assertEqual(read_output['message'], f'{model["name"]["lower_case"]} {created_model_id} not found', f'Read after delete for {model_name} did not return correct message')

    def test_cli_db_commands(self):
        self._test_cli_crud_commands('db')

    def test_cli_http_commands(self):
        self._test_cli_crud_commands('http')


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
