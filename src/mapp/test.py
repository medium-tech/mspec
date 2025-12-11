import os
import unittest
import fnmatch
import json
import subprocess
import glob
import re
import multiprocessing
import time
import shutil

from pathlib import Path
from typing import Optional, Generator
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

from mspec.core import load_generator_spec

from dotenv import dotenv_values


def run_cmd(cmd_args, env):
    result = subprocess.run(cmd_args, capture_output=True, text=True, env=env, timeout=10)
    return (cmd_args, result.returncode, result.stdout, result.stderr)

def example_from_model(model:dict, index=0) -> dict:
    data = {}
    for field_name, field in model.get('fields', {}).items():
        try:
            value = field['examples'][index]
        except (IndexError, KeyError):
            raise ValueError(f'No example for field "{model["name"]["pascal_case"]}.{field_name}" at index {index}')
        
        data[field_name] = value

    return data

def model_validation_errors(model:dict) -> Generator[dict, None, None]:
    example = example_from_model(model)

    for field_name, field in model.get('fields', {}).items():
        for invalid_value in field.get('validation_errors', []):
            example[field_name] = invalid_value

            yield example | {field_name: invalid_value}

def request(ctx:dict, method:str, endpoint:str, request_body:Optional[dict]=None) -> tuple[int, dict]:
    """send request and returnn status code and response body as dict"""

    req = Request(
        ctx['MAPP_CLIENT_HOST'] + endpoint,
        method=method, 
        headers=ctx['headers'], 
        data=request_body,
    )

    try:
        with urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            status = response.status

    except TimeoutError as e:
        raise RuntimeError(f'TimeoutError on {method} {endpoint}: {e}')
        
    except HTTPError as e:
        body = e.read().decode('utf-8')
        status = e.code
    
    try:
        response_data = json.loads(body)
        return status, response_data
    except json.JSONDecodeError as e:
        raise RuntimeError(f'Invalid JSON from {method} {endpoint}, resp length: {len(body)}: {body}')
    
def env_to_string(env:dict) -> str:
    out = ''
    for key, value in env.items():
        if ' ' in value:
            out += f'{key}="{value}"\n'
        else:
            out += f'{key}={value}\n'
    return out


class TestMTemplateApp(unittest.TestCase):
    
    test_dir = 'mapp-tests'

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
    env_file: str | None
    use_cache: bool
    app_type: str = ''
    threads: int = 8

    pool: Optional[multiprocessing.Pool] = None

    crud_db_file = Path(f'{test_dir}/test_crud_db.sqlite3')
    crud_envfile = Path(f'{test_dir}/crud.env')
    crud_ctx = {}

    pagination_db_file = Path(f'{test_dir}/test_pagination_db.sqlite3')
    pagination_envfile = Path(f'{test_dir}/pagination.env')
    pagination_ctx = {}

    pagination_total_models = 25

    pagination_cases = [
        {'size': 1, 'expected_pages': 25},
        {'size': 5, 'expected_pages': 5},
        {'size': 10, 'expected_pages': 3},
        {'size': 25, 'expected_pages': 1},
    ]

    @classmethod
    def setUpClass(cls):

        print(':: Setting up TestMTemplateApp')

        # delete old files #
    
        if not cls.use_cache:
            shutil.rmtree(cls.test_dir, ignore_errors=True)

        os.makedirs(cls.test_dir, exist_ok=True)

        pagination_db_exists = cls.pagination_db_file.exists()
        
        #
        # create test env files
        #

        # base env #

        env_vars = dotenv_values(cls.env_file)

        # crud env file #

        default_host = cls.spec['client']['default_host']
        default_port = int(default_host.split(':')[-1])
        crud_port = default_port + 1
        crud_env = dict(env_vars)
        crud_env['MAPP_SERVER_PORT'] = str(crud_port)
        crud_env['MAPP_CLIENT_HOST'] = f'http://localhost:{crud_port}'
        crud_env['MAPP_DB_URL'] = str(cls.crud_db_file.resolve())

        with open(cls.crud_envfile, 'w') as f:
            f.write(env_to_string(crud_env))

        cls.crud_ctx = os.environ.copy()
        cls.crud_ctx['MAPP_ENV_FILE'] = str(cls.crud_envfile.resolve())
        cls.crud_ctx.update(crud_env)

        # pagination env file #

        pagination_port = default_port + 2
        pagination_env = dict(env_vars)
        pagination_env['MAPP_SERVER_PORT'] = str(pagination_port)
        pagination_env['MAPP_CLIENT_HOST'] = f'http://localhost:{pagination_port}'
        pagination_env['MAPP_DB_URL'] = str(cls.pagination_db_file.resolve())

        with open(cls.pagination_envfile, 'w') as f:
            f.write(env_to_string(pagination_env))

        cls.pagination_ctx = os.environ.copy()
        cls.pagination_ctx['MAPP_ENV_FILE'] = str(cls.pagination_envfile.resolve())
        cls.pagination_ctx.update(pagination_env)

        # open process pool #

        cls.pool = multiprocessing.Pool(processes=cls.threads)

        """
        Testing Table Creation

        There are two cli commands to create tables in MAPP:
            - mapp create-tables
            - mapp <module> <model> db create-table

        The first command creates all tables for all models in all modules.
        The second command creates all tables for a specific model.

        In these tests we create 2 environments, one for testing CRUD ops
        and one for testing pagination. We use the first command to create
        tables for the CRUD environment, and the second command to create
        tables for the pagination environment. This allows us to test both
        methods of table creation.

        --use-cache can be used to skip recreating the pagination db as it is
        expensive seed. This is fine for development testing, but full testing
        should be done without the flag to ensure table creation works from scratch.
        """

        # create crud table #

        crud_create_tables_cmd = cls.cmd + ['create-tables']
        crud_result = subprocess.run(crud_create_tables_cmd, capture_output=True, text=True, env=cls.crud_ctx)
        if crud_result.returncode != 0:
            raise RuntimeError(f'Error creating tables for crud db: {crud_result.stdout + crud_result.stderr}')
        
        try:
            crud_output = json.loads(crud_result.stdout)
            assert crud_output['acknowledged'] is True
            assert crud_output['message'] == 'All tables created or already existed.'
        except AssertionError as e:
            raise RuntimeError(f'AssertionError {e} while creating table for crud db {module_name_kebab}.{model_name_kebab}: {crud_result.stdout + crud_result.stderr}')

        # setup tables in test dbs #

        print('  :: Creating tables in test dbs ::')
        for module in cls.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                if model['hidden'] is True:
                    continue
                
                model_name_snake = model['name']['snake_case']
                model_name_kebab = model['name']['kebab_case']

                create_table_args = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create-table']

                # create pagination table #
                
                if not pagination_db_exists:
                    result = subprocess.run(create_table_args, capture_output=True, text=True, env=cls.pagination_ctx)
                    if result.returncode != 0:
                        raise RuntimeError(f'Error creating table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')
                    
                    try:
                        pagination_output = json.loads(result.stdout)
                        assert pagination_output['acknowledged'] is True
                        assert model_name_snake in pagination_output['message']
                    except AssertionError as e:
                        raise RuntimeError(f'AssertionError {e} while creating table for pagination db {module_name_kebab}.{model_name_kebab}: {result.stdout + result.stderr}')
        
        # seed pagination db #

        if cls.use_cache and pagination_db_exists:
            print('  :: Using cached pagination db ::')
        else:
            print(f'  :: Seeding pagination db ::')
            seed_jobs = []
            for module in cls.spec['modules'].values():
                module_name_kebab = module['name']['kebab_case']

                for model in module['models'].values():
                    if model['hidden'] is True:
                        continue

                    model_name_kebab = model['name']['kebab_case']

                    for _ in range(cls.pagination_total_models):
                        example_model = example_from_model(model, index=0)
                        seed_cmd = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create', json.dumps(example_model)]
                        seed_jobs.append((seed_cmd, cls.pagination_ctx))

            results = cls.pool.starmap(run_cmd, seed_jobs)

            for (cmd_args, code, stdout, stderr) in results:
                if code != 0:
                    raise RuntimeError(f':: ERROR seeding table for pagination db :: COMMAND :: {" ".join(cmd_args)} :: OUTPUT :: {stdout + stderr}')
            
        # delete server logs #

        for log_file in glob.glob(f'{cls.test_dir}/test_server_*.log'):
            try:
                Path(log_file).unlink()
            except FileNotFoundError:
                pass

        # create server configs #

        crud_server_cmd = cls.cmd + ['server']
        pagination_server_cmd = cls.cmd + ['server']

        if cls.app_type == 'python':
            with open('uwsgi.yaml', 'r') as f:
                uwsgi_config = f.read()

            port_pattern = r'http:\s*:\d+'
            pid_file_pattern = r'safe-pidfile:\s*.+'
            stats_pattern = r'stats:\s*.+'
            logto_pattern = r'logto:\s*.+'

            cls.crud_pidfile = f'{cls.test_dir}/uwsgi_crud.pid'
            cls.pagination_pidfile = f'{cls.test_dir}/uwsgi_pagination.pid'
            cls.crud_stats_socket = f'{cls.test_dir}/stats_crud.socket'
            cls.crud_log_file = f'{cls.test_dir}/server_crud.log'

            cls.crud_uwsgi_config = f'{cls.test_dir}/uwsgi_crud.yaml'
            cls.pagination_uwsgi_config = f'{cls.test_dir}/uwsgi_pagination.yaml'
            cls.pagination_stats_socket = f'{cls.test_dir}/stats_pagination.socket'
            cls.pagination_log_file = f'{cls.test_dir}/server_pagination.log'
            crud_server_cmd = ['./server.sh', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config]
            pagination_server_cmd = ['./server.sh', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config]

            with open(cls.crud_uwsgi_config, 'w') as f:
                crud_uwsgi_config = re.sub(port_pattern, f'http: :{crud_port}', uwsgi_config)
                crud_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.crud_pidfile}', crud_uwsgi_config)
                crud_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.crud_stats_socket}', crud_uwsgi_config)
                crud_uwsgi_config = re.sub(logto_pattern, f'logto: {cls.crud_log_file}', crud_uwsgi_config)
                f.write(crud_uwsgi_config)
            
            with open(cls.pagination_uwsgi_config, 'w') as f:
                pagination_uwsgi_config = re.sub(port_pattern, f'http: :{pagination_port}', uwsgi_config)
                pagination_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.pagination_pidfile}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.pagination_stats_socket}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(logto_pattern, f'logto: {cls.pagination_log_file}', pagination_uwsgi_config)
                f.write(pagination_uwsgi_config)
        
        # start servers #

        print('  :: Starting server processes ::')

        cls.server_processes:list[subprocess.Popen] = []

        process = subprocess.Popen(crud_server_cmd, env=cls.crud_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cls.server_processes.append(process)
        print('    :: ', ' '.join(crud_server_cmd))

        process = subprocess.Popen(pagination_server_cmd, env=cls.pagination_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cls.server_processes.append(process)
        print('    :: ', ' '.join(pagination_server_cmd))
        time.sleep(1)
        print('  :: Setup complete ::')

        print(':: test progress :: ', end='', flush=True)
    
    @classmethod
    def tearDownClass(cls):

        print('\n:: Tearing down TestMTemplateApp')

        # stop pool #

        print('  :: Closing process pool ::')

        if cls.pool:
            cls.pool.close()
            cls.pool.join()
        
        if cls.app_type == 'python':
            try:
                subprocess.run(['./server.sh', 'stop', '--pid-file', cls.crud_pidfile], env=cls.crud_ctx, check=True, capture_output=True, timeout=15)
                subprocess.run(['./server.sh', 'stop', '--pid-file', cls.pagination_pidfile], env=cls.pagination_ctx, check=True, capture_output=True, timeout=15)
            except subprocess.TimeoutExpired:
                print('    :: Timeout expired while stopping servers ::')
            except subprocess.CalledProcessError as e:
                print(f'    :: Error stopping servers: {e} :: {e.output} :: {e.stderr} ::')

        # stop servers and capture logs #

        for process in cls.server_processes:
            print(f'  :: Stopping server process {process.pid} ::')
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=10)
                with open(f'{cls.test_dir}/test_server_{process.pid}_stdout.log', 'w') as f:
                    f.write(stdout)
                with open(f'{cls.test_dir}/test_server_{process.pid}_stderr.log', 'w') as f:
                    f.write(stderr)
            except subprocess.TimeoutExpired:
                print('    :: Server process did not terminate in time, killing process ::')
                process.kill()
                stdout, stderr = process.communicate()
                with open(f'{cls.test_dir}/test_server_{process.pid}_stdout.log', 'w') as f:
                    f.write(stdout)
                with open(f'{cls.test_dir}/test_server_{process.pid}_stderr.log', 'w') as f:
                    f.write(stderr)
            except Exception as e:
                print(f'Error capturing server process {process.pid} output: {e}')

            if process.returncode is not None and process.returncode > 0:
                print(f'    :: Server process {process.pid} exited with code {process.returncode} ::')
        
        print(':: Teardown complete ::')

    def _run_cmd(self, cmd:list[str], expected_code=0, env:Optional[dict[str, str]] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(cmd)}" output: {result.stdout + result.stderr}'
        self.assertEqual(result.returncode, expected_code, msg)
        return result
    
    def _check_servers_running(self):
        error = False
        for process in self.server_processes:
            retcode = process.poll()
            if retcode is not None:
                error = True

        self.assertFalse(error, 'One or more server processes have exited unexpectedly')

    # builtin - auth tests #

    def _test_user_auth_flow(self, ctx:dict, io_type:str):
        """
        test auth command flow via cli <io type> command

        ./mapp auth delete-user <io type>
            * expect error
        ./mapp auth current-user <io type>
            * expect error

        ./mapp auth create-user <io type> {"name": "brad", ...}
        ./mapp auth login-user <io type> {"email": "...", ...}
        ./mapp auth current-user <io type>
        ./mapp auth logout-user <io type> {"mode": "current"}
        ./mapp auth current-user <io type>
            * expect error
        ./mapp auth login-user <io type> {"email": "...", ...}
        ./mapp auth delete-user <io type>
        ./mapp auth current-user <io type>
            * expect error
        """
        # Setup
        cmd = self.cmd
        env = self.crud_ctx.copy()
        user_name = 'alice'
        user_email = f'alice@{io_type}.com'
        user_password = 'testpass123'
        
        # Helper to run a command and return output
        def run_auth_cmd(args, input_data=None, expected_code=0):
            if input_data is not None:
                result = subprocess.run(args, input=input_data, capture_output=True, text=True, env=env)
            else:
                result = subprocess.run(args, capture_output=True, text=True, env=env)
            msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(args)}" output: {result.stdout + result.stderr}'
            self.assertEqual(result.returncode, expected_code, msg)
            return result

        # 1. delete-user (should error)
        result = run_auth_cmd(cmd + ["auth", "delete-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 2. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 3. create-user
        create_input = json.dumps({"name": user_name, "email": user_email, "password": user_password, "password_confirm": user_password})
        result = run_auth_cmd(cmd + ["auth", "create-user", io_type, create_input])
        self.assertIn(user_email, result.stdout)

        # 4. login-user
        login_input = json.dumps({"email": user_email, "password": user_password})
        result = run_auth_cmd(cmd + ["auth", "login-user", io_type, login_input])
        self.assertIn("access_token", result.stdout)

        # 5. current-user (should succeed)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type])
        self.assertIn(user_email, result.stdout)

        # 6. logout-user (current)
        logout_input = json.dumps({"mode": "current"})
        result = run_auth_cmd(cmd + ["auth", "logout-user", io_type, logout_input])
        self.assertIn("logged out", result.stdout.lower())

        # 7. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

        # 8. login-user (again)
        result = run_auth_cmd(cmd + ["auth", "login-user", io_type, login_input])
        self.assertIn("access_token", result.stdout)

        # 9. delete-user
        result = run_auth_cmd(cmd + ["auth", "delete-user", io_type])
        self.assertIn("deleted", result.stdout.lower())

        # 10. current-user (should error)
        result = run_auth_cmd(cmd + ["auth", "current-user", io_type], expected_code=1)
        self.assertIn("error", result.stdout.lower())

    def test_cli_run_auth_flow(self):
        self._test_user_auth_flow(self.crud_ctx, "run")
    
    def test_cli_http_auth_flow(self):
        """
        test auth command flow via cli http command
        
        ./mapp auth delete-user http
            * expect error
        ./mapp auth current-user http
            * expect error

        ./mapp auth create-user http {"name": "brad", ...}
        ./mapp auth login-user http {"email": "...", ...}
        ./mapp auth current-user http
        ./mapp auth logout-user http {"mode": "current"}
        ./mapp auth current-user http
            * expect error
        ./mapp auth login-user http {"email": "...", ...}
        ./mapp auth delete-user http
        ./mapp auth current-user http
            * expect error
        """

    def test_server_auth_endpoints(self):
        pass

    # crud tests #

    def _test_cli_crud_commands(self, command_type:str):

        logged_out_ctx = self.crud_ctx.copy()

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model_name, model in module['models'].items():
                hidden = model['hidden']
                require_login = model['auth']['require_login']

                model_name_kebab = model['name']['kebab_case']

                model_db_args = self.cmd + [module_name_kebab, model_name_kebab, command_type]

                # create #

                example_to_create = example_from_model(model)
                create_args = model_db_args + ['create', json.dumps(example_to_create)]

                if hidden:
                    result = self._run_cmd(create_args, env=self.crud_ctx, expected_code=2)
                else:
                    if require_login:
                        logged_out_result = self._run_cmd(create_args, env=logged_out_ctx, expected_code=1)

                    result = self._run_cmd(create_args, env=self.crud_ctx)
                    created_model = json.loads(result.stdout)

                    created_model_id = created_model.pop('id')  # remove id for comparison
                    self.assertEqual(created_model, example_to_create, f'Created {model_name} does not match example data')

                # read #

                read_args = model_db_args + ['read', str(created_model_id)]

                if hidden:
                    result = self._run_cmd(read_args, env=self.crud_ctx, expected_code=2)
                else:
                    if require_login:
                        logged_out_result = self._run_cmd(read_args, env=logged_out_ctx, expected_code=1)

                    result = self._run_cmd(read_args, env=self.crud_ctx)
                    read_model = json.loads(result.stdout)
                    read_model_id = read_model.pop('id')
                    self.assertEqual(read_model, example_to_create, f'Read {model_name} does not match example data')
                    self.assertEqual(read_model_id, created_model_id, f'Read {model_name} ID does not match created ID')

                # update #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                
                update_args = model_db_args + ['update', created_model_id, json.dumps(updated_example)]
            
                if hidden:
                    result = self._run_cmd(update_args, env=self.crud_ctx, expected_code=2)
                else:
                    if require_login:
                        logged_out_result = self._run_cmd(update_args, env=logged_out_ctx, expected_code=1)

                    result = self._run_cmd(update_args, env=self.crud_ctx)
                    updated_model = json.loads(result.stdout)
                    updated_model_id = updated_model.pop('id')
                    self.assertEqual(updated_model, updated_example, f'Updated {model_name} does not match updated example data')
                    self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} ID does not match created ID')

                # delete #

                delete_args = model_db_args + ['delete', str(created_model_id)]

                if hidden:
                    result = self._run_cmd(delete_args, env=self.crud_ctx, expected_code=2)
                else:
                    if require_login:
                        logged_out_result = self._run_cmd(delete_args, env=logged_out_ctx, expected_code=1)

                    result = self._run_cmd(delete_args, env=self.crud_ctx)
                    delete_output = json.loads(result.stdout)
                    self.assertEqual(delete_output['acknowledged'], True, f'Delete {model_name} ID did not return acknowledgement')
                    expected_delete_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
                    self.assertTrue(delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message')

                    # confirm delete is idempotent #

                    result = self._run_cmd(model_db_args + ['delete', str(created_model_id)], env=self.crud_ctx)
                    delete_output = json.loads(result.stdout)
                    self.assertTrue(delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message')

                # read after delete #

                if not hidden:
                    result = self._run_cmd(model_db_args + ['read', str(created_model_id)], expected_code=1, env=self.crud_ctx)
                    try:
                        read_output_err = json.loads(result.stdout)['error']
                        self.assertEqual(read_output_err['code'], 'NOT_FOUND', f'Read after delete for {model_name} did not return NOT_FOUND code for id {created_model_id}')
                        self.assertEqual(read_output_err['message'], f'{model["name"]["snake_case"]} {created_model_id} not found', f'Read after delete for {model_name} did not return correct message for id {created_model_id}')
                    except KeyError as e:
                        raise RuntimeError(f'KeyError {e} while reading after delete for {model_name} id {created_model_id}: {result.stdout + result.stderr}')
                    except json.JSONDecodeError as e:
                        raise RuntimeError(f'JSONDecodeError {e} while reading after delete for {model_name} id {created_model_id}: {result.stdout + result.stderr}')

    def test_cli_db_crud(self):
        self._test_cli_crud_commands('db')

    def test_cli_http_crud(self):
        self._test_cli_crud_commands('http')

    def test_server_crud_endpoints(self):

        self._check_servers_running()
        
        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        ctx.update(self.crud_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        logged_out_ctx.update(self.crud_ctx)
        
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():

                hidden = model['hidden']
                require_login = model['auth']['require_login']
                model_name_kebab = model['name']['kebab_case']

                #
                # create
                #

                example_to_create = example_from_model(model)
                create_args = [
                    'POST',
                    f'/api/{module_name_kebab}/{model_name_kebab}',
                    json.dumps(example_to_create).encode()
                ]

                if require_login:
                    created_status, data = request(
                        logged_out_ctx,
                        *create_args
                    )
                    self.assertEqual(created_status, 401, f'Create {model_name} without login did not return 401 Unauthorized, response: {data}')

                # send request #

                created_status, created_model = request(
                    ctx,
                    *create_args
                )

                # confirm response #

                if hidden:
                    self.assertEqual(created_status, 404, f'Create hidden {model_name} did not return 404 Not Found, response: {created_model}')

                else:
                    self.assertEqual(created_status, 200, f'Create {model_name} did not return status 200 OK, response: {created_model}')
                    created_model_id = created_model.pop('id')  # remove id for comparison
                    self.assertEqual(created_model, example_to_create, f'Created {model_name} (id: {created_model_id}) does not match example data')

                #
                # read
                #

                if require_login:
                    read_status, data = request(
                        logged_out_ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{1}',
                        None
                    )
                    self.assertEqual(read_status, 401, f'Read {model_name} without login did not return 401 Unauthorized, response: {data}')

                # send request #

                read_status, read_model = request(
                    ctx,
                    'GET',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    None
                )

                # confirm response #

                if hidden:
                    self.assertEqual(read_status, 404, f'Read hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {read_model}')

                else:
                    self.assertEqual(read_status, 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}')
                    read_model_id = read_model.pop('id')
                    self.assertEqual(read_model, example_to_create, f'Read {model_name} id: {read_model_id} does not match example data')
                    self.assertEqual(read_model_id, created_model_id, f'Read {model_name} id: {read_model_id} does not match created id: {created_model_id}')

                #
                # update
                #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                
                if require_login:
                    update_status, data = request(
                        logged_out_ctx,
                        'PUT',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        json.dumps(updated_example).encode()
                    )
                    self.assertEqual(update_status, 401, f'Update {model_name} without login did not return 401 Unauthorized, response: {data}')
                
                # send request #

                updated_status, updated_model = request(
                    ctx,
                    'PUT',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    json.dumps(updated_example).encode()
                )

                # confirm response #

                if hidden:
                    self.assertEqual(updated_status, 404, f'Update hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {updated_model}')

                else:
                    self.assertEqual(updated_status, 200, f'Update {model_name} id: {created_model_id} did not return status 200 OK, response: {updated_model}')
                    updated_model_id = updated_model.pop('id')
                    self.assertEqual(updated_model, updated_example, f'Updated {model_name} id: {updated_model_id} does not match updated example data')
                    self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} id: {updated_model_id} does not match created id: {created_model_id}')

                #
                # delete
                #

                if require_login:
                    delete_status, data = request(
                        logged_out_ctx,
                        'DELETE',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.assertEqual(delete_status, 401, f'Delete {model_name} without login did not return 401 Unauthorized, response: {data}')

                # send request #

                delete_status, delete_output = request(
                    ctx,
                    'DELETE',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                    None
                )

                # confirm response #

                if hidden:
                    self.assertEqual(delete_status, 404, f'Delete hidden {model_name} id: {created_model_id} did not return 404 Not Found, response: {delete_output}')

                else:
                    self.assertEqual(delete_status, 200, f'Delete {model_name} id: {created_model_id} did not return status 200 OK, response: {delete_output}')
                    self.assertIn('acknowledged', delete_output, f'Delete {model_name} id: {created_model_id} did not return acknowledgement field')
                    self.assertTrue(delete_output['acknowledged'], f'Delete {model_name} id: {created_model_id} did not return acknowledged=True')
                    self.assertIn('message', delete_output, f'Delete {model_name} id: {created_model_id} did not return message field')
                    expected_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
                    self.assertTrue(delete_output['message'].startswith(expected_msg), f'Delete {model_name} id: {created_model_id} did not return correct message')

                # confirm delete is idempotent #

                if not hidden:

                    delete_status, delete_output = request(
                        ctx,
                        'DELETE',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.assertEqual(delete_status, 200, f'Delete (2nd) {model_name} id: {created_model_id} did not return status 200 OK, response: {delete_output}')
                    self.assertIn('acknowledged', delete_output, f'Delete {model_name} id: {created_model_id} did not return acknowledgement field')
                    self.assertTrue(delete_output['acknowledged'], f'Delete {model_name} id: {created_model_id} did not return acknowledged=True')
                    self.assertIn('message', delete_output, f'Delete {model_name} id: {created_model_id} did not return message field')
                    expected_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
                    self.assertTrue(delete_output['message'].startswith(expected_msg), f'Delete {model_name} id: {created_model_id} did not return correct message')

                    # read after delete #

                    re_read_status, re_read_model = request(
                        ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                
                    self.assertEqual(re_read_status, 404, f'Read after delete for {model_name} id: {created_model_id} did not return 404 Not Found, resp: {re_read_model}')
                    self.assertEqual(re_read_model.get('error', {}).get('code', '-'), 'NOT_FOUND', f'Read after delete for {model_name} id: {created_model_id} did not return not_found code, resp: {re_read_model}')

    # pagination tests #

    def _test_cli_pagination_command(self, command_type:str):

        # init tests #

        logged_out_ctx = self.pagination_ctx.copy()
        commands = []
        test_cases = []

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():

                model_name_kebab = model['name']['kebab_case']
                model_list_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'list']
    
                if model['auth']['require_login']:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=1, env=logged_out_ctx)

                if model['hidden'] is True:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=2, env=self.pagination_ctx)
                    continue

                for case in self.pagination_cases:
                    size = case['size']
                    expected_pages = case['expected_pages']
                    offset = 0

                    for page in range(expected_pages):
                        commands.append((model_list_command + [f'--size={size}', f'--offset={offset}'], self.pagination_ctx))
                        test_cases.append((module_name_kebab, model_name_kebab, size, expected_pages, page, offset))
                        offset += size

        # run tests #

        results = self.pool.starmap(run_cmd, commands)

        # confirm results #
        
        grouped = defaultdict(list)
        for (module_name_kebab, model_name_kebab, size, expected_pages, page, offset), (cmd_args, code, stdout, stderr) in zip(test_cases, results):
            key = (module_name_kebab, model_name_kebab, size, expected_pages)
            grouped[key].append((page, offset, code, stdout, stderr))

        for (module_name_kebab, model_name_kebab, size, expected_pages), pages in grouped.items():
            pages.sort()
            page_count = 0
            for page, offset, code, stdout, stderr in pages:
                response = json.loads(stdout)
                self.assertEqual(response['total'], self.pagination_total_models, f'Pagination for {model_name_kebab} page {page} returned incorrect total')
                items = response['items']
                self.assertLessEqual(len(items), size, f'Pagination for {model_name_kebab} returned more items than size {size}')
                if len(items) == 0:
                    break
                page_count += 1
            self.assertEqual(page_count, expected_pages, f'Pagination for {model_name_kebab} returned {page_count} pages, expected {expected_pages}')

    def test_cli_db_pagination(self):
        self._test_cli_pagination_command('db')

    def test_cli_http_pagination(self):
        self._test_cli_pagination_command('http')

    def test_server_pagination_endpoints(self):

        self._check_servers_running()
        
        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        ctx.update(self.pagination_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        logged_out_ctx.update(self.pagination_ctx)
        
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():
                hidden = model['hidden']
                model_name_kebab = model['name']['kebab_case']

                if model['auth']['require_login']:
                    status, response = request(
                        logged_out_ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}?size=10&offset=0',
                        None
                    )
                    self.assertEqual(status, 401, f'Pagination for {model_name_kebab} without login did not return 401 Unauthorized, response: {response}')

                for case in self.pagination_cases:
                    size = case['size']
                    expected_pages = case['expected_pages']

                    # paginate #

                    offset = 0
                    page_count = 0

                    while True:
                        status, response = request(
                            ctx,
                            'GET',
                            f'/api/{module_name_kebab}/{model_name_kebab}?size={size}&offset={offset}',
                            None
                        )

                        if hidden:
                            self.assertEqual(status, 404, f'Pagination for hidden {model_name_kebab} did not return 404 Not Found, response: {response}')
                            break

                        self.assertEqual(status, 200, f'Pagination for {model_name_kebab} page {page_count} did not return status 200 OK, response: {response}')
                        self.assertEqual(response['total'], self.pagination_total_models, f'Pagination for {model_name_kebab} page {page_count} returned incorrect total')
 
                        items = response['items']
                        self.assertLessEqual(len(items), size, f'Pagination for {model_name_kebab} returned more items than size {size}')
                        
                        if len(items) == 0:
                            break

                        page_count += 1

                        offset += size

                    if hidden:
                        break

                    self.assertEqual(page_count, expected_pages, f'Pagination for {model_name} returned {page_count} pages, expected {expected_pages}')
      
    # validation tests #

    def _test_cli_validation_error(self, module_name_kebab:str, model:dict, command_type:str):

        if model['hidden'] is True:
            return

        model_name_kebab = model['name']['kebab_case']

        # create model to attempt to update with invalid data #

        example_to_update = example_from_model(model)
        args = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(example_to_update)]
        result = self._run_cmd(args, env=self.crud_ctx)
        update_model_id = str(json.loads(result.stdout)['id'])

        for invalid_example in model_validation_errors(model):
            model_name_kebab = model['name']['kebab_case']

            # create #

            model_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(invalid_example)]
            result = self._run_cmd(model_command, expected_code=1, env=self.crud_ctx)

            error_output = json.loads(result.stdout)
            self.assertEqual(error_output['code'], 'validation_error', f'Expected validation_error code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {error_output["code"]}')
            self.assertTrue(error_output['message'].startswith('Validation Error: '), f'Expected validation_error message for {model["name"]["pascal_case"]} with invalid data {invalid_example} to start with "Validation error: ", got {error_output["message"]}')

            # update #

            model_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'update', update_model_id, json.dumps(invalid_example)]
            result = self._run_cmd(model_command, expected_code=1, env=self.crud_ctx)
            error_output = json.loads(result.stdout)
            self.assertEqual(error_output['code'], 'validation_error', f'Expected validation_error code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {error_output["code"]}')
            self.assertTrue(error_output['message'].startswith('Validation Error: '), f'Expected validation_error message for {model["name"]["pascal_case"]} with invalid data {invalid_example} to start with "Validation error: ", got {error_output["message"]}')

        # read back original example to ensure it was not modified #

        result = self._run_cmd(self.cmd + [module_name_kebab, model_name_kebab, command_type, 'read', update_model_id], env=self.crud_ctx)
        read_model = json.loads(result.stdout)
        del read_model['id']
        self.assertEqual(read_model, example_to_update, f'Read {model["name"]["pascal_case"]} does not match original example data after validation error tests')

    def test_cli_db_validation_error(self):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                self._test_cli_validation_error(module_name_kebab, model, 'db')

    def test_cli_http_validation_error(self):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                self._test_cli_validation_error(module_name_kebab, model, 'http')

    def test_server_validation_error(self):
        self._check_servers_running()
        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        ctx.update(self.crud_ctx)

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model in module['models'].values():
                if model['hidden'] is True:
                    continue
                model_name_kebab = model['name']['kebab_case']

                # create a valid model to update with invalid data
                example_to_update = example_from_model(model)
                create_status, create_resp = request(
                    ctx,
                    'POST',
                    f'/api/{module_name_kebab}/{model_name_kebab}',
                    json.dumps(example_to_update).encode()
                )
                self.assertEqual(create_status, 200, f'Create for validation error test failed: {create_resp}')
                update_model_id = str(create_resp['id'])

                for invalid_example in model_validation_errors(model):
                    # create (invalid)
                    status, output = request(
                        ctx,
                        'POST',
                        f'/api/{module_name_kebab}/{model_name_kebab}',
                        json.dumps(invalid_example).encode()
                    )
                    self.assertEqual(status, 400, f'Expected 400 for invalid create, got {status}, resp: {output}')
                    self.assertEqual(
                        output['code'], 
                        'VALIDATION_ERROR', 
                        f'Expected VALIDATION_ERROR code for {model_name_kebab} with invalid data {invalid_example}, got {output}'
                    )
                    self.assertTrue(
                        output['message'].startswith('Validation Error: '), 
                        f'Unexpected message for {model_name_kebab} with invalid data {invalid_example}, got {output}'
                    )

                    # update (invalid)
                    status, output = request(
                        ctx,
                        'PUT',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{update_model_id}',
                        json.dumps(invalid_example).encode()
                    )
                    self.assertEqual(status, 400, f'Expected 400 for invalid update, got {status}, resp: {output}')
                    self.assertEqual(
                        output['code'], 
                        'VALIDATION_ERROR', 
                        f'Expected VALIDATION_ERROR code for {model_name_kebab} with invalid data {invalid_example}, got {output}'
                    )
                    self.assertTrue(
                        output['message'].startswith('Validation Error: '), 
                        f'Unexpected message for {model_name_kebab} with invalid data {invalid_example}, got {output}'
                    )

                # read back original example to ensure it was not modified
                status, read_model = request(
                    ctx,
                    'GET',
                    f'/api/{module_name_kebab}/{model_name_kebab}/{update_model_id}',
                    None
                )
                self.assertEqual(status, 200, f'Read after validation error for {model["name"]["pascal_case"]} did not return 200 OK, resp: {read_model}')
                del read_model['id']
                self.assertEqual(read_model, example_to_update, f'Read after validation error for {model["name"]["pascal_case"]} does not match original example data')

    # other tests #

    def test_cli_help_menus(self):

        help_jobs = []

        project_kebab = self.spec['project']['name']['kebab_case']
        global_help_text = ':: ' + project_kebab

        # global help
        for global_help_arg in ['help', '--help', '-h']:
            args = self.cmd + [global_help_arg]
            env = self.crud_ctx
            def assertion(stdout, stderr, code, args=args):
                self.assertEqual(code, 0, f"Global help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                self.assertIn(global_help_text, stdout)
            help_jobs.append((args, env, assertion))

        # create tables help
        create_tables_help_text = global_help_text + ' :: create-tables'
        for create_tables_help_arg in ['help', '--help', '-h']:
            args = self.cmd + ['create-tables', create_tables_help_arg]
            env = self.crud_ctx
            def assertion(stdout, stderr, code, args=args):
                self.assertEqual(code, 0, f"Create-tables help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                self.assertIn(create_tables_help_text, stdout)
            help_jobs.append((args, env, assertion))

        # module/model/io/op help
        for module in self.spec['modules'].values():
            module_help_text = global_help_text + f' :: {module["name"]["kebab_case"]}'
            for module_help_arg in ['help', '--help', '-h']:
                args = self.cmd + [module['name']['kebab_case'], module_help_arg]
                env = self.crud_ctx
                def assertion(stdout, stderr, code, args=args, expected=module_help_text):
                    self.assertEqual(code, 0, f"Module help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                    self.assertIn(expected, stdout)
                help_jobs.append((args, env, assertion))

            for model in module.get('models', {}).values():
                if model['hidden']:
                    continue
                model_help_text = module_help_text + f' :: {model["name"]["kebab_case"]}'
                for model_help_arg in ['help', '--help', '-h']:
                    args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], model_help_arg]
                    env = self.crud_ctx
                    def assertion(stdout, stderr, code, args=args, expected=model_help_text):
                        self.assertEqual(code, 0, f"Model help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                        self.assertIn(expected, stdout)
                    help_jobs.append((args, env, assertion))

                for io in ['db', 'http']:
                    io_help_text = model_help_text + f' :: {io}'
                    for io_help_arg in ['help', '--help', '-h']:
                        args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], io, io_help_arg]
                        env = self.crud_ctx
                        def assertion(stdout, stderr, code, args=args, expected=io_help_text):
                            self.assertEqual(code, 0, f"IO help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                            self.assertIn(expected, stdout)
                        help_jobs.append((args, env, assertion))

                    crud_ops = ['create', 'read', 'update', 'delete', 'list']
                    if io == 'db':
                        ops_to_run = crud_ops + ['create-table']
                    else:
                        ops_to_run = crud_ops

                    for op in ops_to_run:
                        op_help_text = io_help_text + f' :: {op}'
                        for op_help_arg in ['help', '--help', '-h']:
                            args = self.cmd + [module['name']['kebab_case'], model['name']['kebab_case'], io, op, op_help_arg]
                            env = self.crud_ctx
                            def assertion(stdout, stderr, code, args=args, expected=op_help_text):
                                self.assertEqual(code, 0, f"Op help failed: {' '.join(args)}\n{stdout}\n{stderr}")
                                self.assertIn(expected, stdout.replace('\n', ''))
                            help_jobs.append((args, env, assertion))

        with multiprocessing.Pool(processes=self.threads) as pool:
            results = pool.starmap(run_cmd, [(args, env) for args, env, _ in help_jobs])

        for (args, code, stdout, stderr), (_, _, assertion) in zip(results, help_jobs):
            assertion(stdout, stderr, code, args)
    

def test_spec(spec_path:str|Path, cli_args:list[str], host:str|None, env_file:str|None, use_cache:bool=False, app_type:str='', verbose:bool=False) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings')

    test_suite = unittest.TestSuite()
    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host
    TestMTemplateApp.env_file = env_file
    TestMTemplateApp.use_cache = use_cache
    TestMTemplateApp.app_type = app_type

    # Support test filtering by name
    test_filters = getattr(test_spec, '_test_filters', None)
    loader = unittest.TestLoader()
    if test_filters:

        # Only add tests matching any filter pattern (glob-style, case-insensitive)
        for test_name in loader.getTestCaseNames(TestMTemplateApp):
            if any(fnmatch.fnmatchcase(test_name.lower(), pat.lower()) for pat in test_filters):
                test_case = TestMTemplateApp(test_name)
                test_case.maxDiff = None
                test_suite.addTest(test_case)
    else:
        tests = loader.loadTestsFromTestCase(TestMTemplateApp)
        for test in tests:
            test.maxDiff = None
            test_suite.addTest(test)

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(test_suite)

    TestMTemplateApp.spec = None
    TestMTemplateApp.cmd = None
    TestMTemplateApp.host = None

    return result.wasSuccessful()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test mapp spec app', prog='mapp.test')
    parser.add_argument('spec', type=str, help='spec file to test')
    parser.add_argument('--cmd', type=str, nargs='*', required=True, help='CLI command for generated app')
    parser.add_argument('--env-file', type=str, required=True, help='path to .env file to load for tests')
    parser.add_argument('--host', type=str, default=None, help='host for http client in tests (if host diff than in spec file)')
    parser.add_argument('--test-filter', type=str, nargs='*', default=None, help='Glob pattern(s) to filter test names (e.g. test_cli_db*)')
    parser.add_argument('--use-cache', action='store_true', help='Use cached test resources if available')
    parser.add_argument('--app-type', type=str, default='', help='Supply "python" to run setup for python apps')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    if args.test_filter:
        # Attach filter patterns to test_spec function for access
        test_spec._test_filters = args.test_filter
    else:
        test_spec._test_filters = None

    test_spec(args.spec, args.cmd, args.host, args.env_file, args.use_cache, args.app_type, args.verbose)