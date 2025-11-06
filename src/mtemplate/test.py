import unittest
import json
import subprocess
import glob

from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

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

def request(ctx:dict, method:str, endpoint:str, request_body:Optional[dict]=None) -> dict:

    request = Request(
        ctx['MAPP_CLIENT_HOST'] + endpoint,
        method=method, 
        headers=ctx['headers'], 
        data=request_body
    )

    with urlopen(request) as response:
        response_body = response.read().decode('utf-8')
        return json.loads(response_body)

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

    crud_db_file = Path('data/test_crud_db.sqlite3')
    crud_ctx = {
        'MAPP_DB_FILE': str(crud_db_file.resolve()),
    }

    pagination_db_file = Path('data/test_pagination_db.sqlite3')
    pagination_ctx = {
        'MAPP_DB_FILE': str(pagination_db_file.resolve()),
    }

    pagination_total_models = 25

    @classmethod
    def setUpClass(cls):

        cls.crud_db_file.parent.mkdir(parents=True, exist_ok=True)

        # delete test db files #

        try:
            cls.crud_db_file.unlink()
        except FileNotFoundError:
            pass

        try:
            cls.pagination_db_file.unlink()
        except FileNotFoundError:
            pass

        # configure ctx #

        default_host = cls.spec['client']['default_host']
        default_port = int(default_host.split(':')[-1])

        crud_port = default_port + 1
        cls.crud_ctx['MAPP_SERVER_PORT'] = str(crud_port)
        cls.crud_ctx['MAPP_CLIENT_HOST'] = f'http://localhost:{crud_port}'

        pagination_port = default_port + 2
        cls.pagination_ctx['MAPP_SERVER_PORT'] = str(pagination_port)
        cls.pagination_ctx['MAPP_CLIENT_HOST'] = f'http://localhost:{pagination_port}'

        # setup tables in test dbs #

        for module in cls.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                model_name_kebab = model['name']['kebab_case']

                create_table_args = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create-table']

                result = subprocess.run(create_table_args, capture_output=True, text=True, env=cls.crud_ctx)
                if result.returncode != 0:
                    raise RuntimeError(f'Error creating table for crud db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')
                
                result = subprocess.run(create_table_args, capture_output=True, text=True, env=cls.pagination_ctx)
                if result.returncode != 0:
                    raise RuntimeError(f'Error creating table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')
        
        # seed pagination db #

        for module in cls.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                model_name_kebab = model['name']['kebab_case']
                for _ in range(cls.pagination_total_models):
                    example_model = example_from_model(model, index=0)
                    result = subprocess.run(
                        cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create', json.dumps(example_model)],
                        text=True,
                        capture_output=True,
                        env=cls.pagination_ctx
                    )
                    if result.returncode != 0:
                        raise RuntimeError(f'Error seeding table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')
        
        # delete server logs #

        for log_file in glob.glob('data/test_server_*.log'):
            try:
                Path(log_file).unlink()
            except FileNotFoundError:
                pass
        
        # start servers #

        cls.server_processes:list[subprocess.Popen] = []

        for ctx in [cls.crud_ctx, cls.pagination_ctx]:
            server_cmd = cls.cmd + ['server']
            process = subprocess.Popen(server_cmd, env=ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            cls.server_processes.append(process)
    
    @classmethod
    def tearDownClass(cls):

        # stop servers and capture logs #

        for process in cls.server_processes:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=10)
                with open(f'data/test_server_{process.pid}_stdout.log', 'w') as f:
                    f.write(stdout)
                with open(f'data/test_server_{process.pid}_stderr.log', 'w') as f:
                    f.write(stderr)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                with open(f'data/test_server_{process.pid}_stdout.log', 'w') as f:
                    f.write(stdout)
                with open(f'data/test_server_{process.pid}_stderr.log', 'w') as f:
                    f.write(stderr)
            except Exception as e:
                print(f'Error capturing server process {process.pid} output: {e}')
        
        # delete test db files #

        try:
            cls.crud_db_file.unlink()
        except FileNotFoundError:
            pass

        try:
            cls.pagination_db_file.unlink()
        except FileNotFoundError:
            pass

    def _run_cmd(self, cmd:list[str], expected_code=0, env:Optional[dict[str, str]] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(cmd)}" output: {result.stdout + result.stderr}'
        self.assertEqual(result.returncode, expected_code, msg)
        return result

    def _test_cli_crud_commands(self, command_type:str):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model_name, model in module['models'].items():
                model_name_kebab = model['name']['kebab_case']

                model_db_args = self.cmd + [module_name_kebab, model_name_kebab, command_type]

                # create #

                example_to_create = example_from_model(model)
                result = self._run_cmd(model_db_args + ['create', json.dumps(example_to_create)], env=self.crud_ctx)
                created_model = json.loads(result.stdout)

                created_model_id = created_model.pop('id')  # remove id for comparison
                self.assertEqual(created_model, example_to_create, f'Created {model_name} does not match example data')

                # read #

                result = self._run_cmd(model_db_args + ['read', str(created_model_id)], env=self.crud_ctx)
                read_model = json.loads(result.stdout)
                read_model_id = read_model.pop('id')
                self.assertEqual(read_model, example_to_create, f'Read {model_name} does not match example data')
                self.assertEqual(read_model_id, created_model_id, f'Read {model_name} ID does not match created ID')

                # update #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                result = self._run_cmd(model_db_args + ['update', created_model_id, json.dumps(updated_example)], env=self.crud_ctx)
                updated_model = json.loads(result.stdout)
                updated_model_id = updated_model.pop('id')
                self.assertEqual(updated_model, updated_example, f'Updated {model_name} does not match updated example data')
                self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} ID does not match created ID')

                # delete #

                result = self._run_cmd(model_db_args + ['delete', str(created_model_id)], env=self.crud_ctx)
                delete_output = json.loads(result.stdout)
                self.assertEqual(delete_output['id'], created_model_id, f'Deleted {model_name} ID does not match created ID')
                self.assertEqual(delete_output['message'], f'deleted {model['name']['lower_case']} {created_model_id}')

                # read after delete #

                result = self._run_cmd(model_db_args + ['read', str(created_model_id)], expected_code=1, env=self.crud_ctx)
                read_output = json.loads(result.stdout)
                self.assertEqual(read_output['code'], 'not_found', f'Read after delete for {model_name} did not return not_found code')
                self.assertEqual(read_output['message'], f'{model['name']['lower_case']} {created_model_id} not found', f'Read after delete for {model_name} did not return correct message')

    def test_cli_db_commands(self):
        self._test_cli_crud_commands('db')

    def test_cli_http_commands(self):
        self._test_cli_crud_commands('http')

    def test_cli_help_menus(self):

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
                self.assertIn(f'{module['name']['pascal_case']} Help', result.stdout)

            # each model in module help #

            for model in module.get('models', {}).values():
                for model_help_arg in ['help', '--help', '-h']:
                    model_help_cmd = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], model_help_arg]
                    result = self._run_cmd(model_help_cmd)
                    self.assertIn(f'{model['name']['pascal_case']} Help', result.stdout)
    
    def test_cli_bad_commands(self):
        pass

    def test_server_crud_endpoints(self):
        
        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        ctx.update(self.crud_ctx)

        # try:
        #     ctx['host'] = self.spec['client']['default_host'] if self.host is None else self.host
        # except KeyError:
        #     raise ValueError('No default_host found in spec and no host provided for testing')
        
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():
                model_name_kebab = model['name']['kebab_case']

                # create #

                example_to_create = example_from_model(model)
                created_model = request(
                    ctx,
                    'POST',
                    f'/api/{module_name_kebab}/{model_name_kebab}',
                    json.dumps(example_to_create).encode()
                )

                created_model_id = created_model.pop('id')  # remove id for comparison
                self.assertEqual(created_model, example_to_create, f'Created {model_name} (id: {created_model_id}) does not match example data')

                # read #

                read_model = request(
                    ctx,
                    'GET',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    None
                )
                read_model_id = read_model.pop('id')
                self.assertEqual(read_model, example_to_create, f'Read {model_name} id: {read_model_id} does not match example data')
                self.assertEqual(read_model_id, created_model_id, f'Read {model_name} id: {read_model_id} does not match created id: {created_model_id}')

                # update #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                updated_model = request(
                    ctx,
                    'PUT',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    json.dumps(updated_example).encode()
                )
                updated_model_id = updated_model.pop('id')
                self.assertEqual(updated_model, updated_example, f'Updated {model_name} id: {updated_model_id} does not match updated example data')
                self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} id: {updated_model_id} does not match created id: {created_model_id}')

                # delete #

                delete_output = request(
                    ctx,
                    'DELETE',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    None
                )
                self.assertEqual(delete_output, {'acknowledged': True}, f'Delete {model_name} id: {created_model_id} did not return acknowledgement')

                # read after delete #

                try:
                    request(
                        ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.fail(f'Read after delete for {model_name} id: {created_model_id} did not raise NotFoundError')
                except HTTPError as e:
                    self.assertEqual(e.code, 404, f'Read after delete for {model_name} id: {created_model_id} did not return 404 Not Found')
                    read_output = json.loads(e.fp.read().decode('utf-8'))
                    self.assertEqual(read_output['code'], 'not_found', f'Read after delete for {model_name} id: {created_model_id} did not return not_found code')

def test_spec(spec_path:str|Path, cli_args:list[str], host:str|None) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings')

    test_suite = unittest.TestSuite()
    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host

    tests = unittest.TestLoader().loadTestsFromTestCase(TestMTemplateApp)
    test_suite.addTests(tests)

    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)

    TestMTemplateApp.spec = None
    TestMTemplateApp.cmd = None
    TestMTemplateApp.host = None

    return result.wasSuccessful()
