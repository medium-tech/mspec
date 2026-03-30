import os
import unittest
import fnmatch
import json
import subprocess
import glob
import re
import multiprocessing
import hashlib
import shutil
import jwt

from pathlib import Path
from copy import deepcopy
from typing import Optional, Generator
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

from mspec.core import load_generator_spec

from dotenv import dotenv_values

def seed_pagination_item(unique_id, base_cmd, seed_cmd, env, require_auth, model_data):
    if require_auth:

        # it will create a user for each item because some models
        # have a max number of items per user.
        # this can be optimized

        # create user #

        user_data = {
            'name': f'user {unique_id}', 
            'email': f'user.{unique_id}@example.com', 
            'password': 'testpass123', 
            'password_confirm': 'testpass123'
        }
        create_user_cmd = base_cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
        result = subprocess.run(create_user_cmd, capture_output=True, text=True, env=env, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f'Error creating user for pagination seeding:\n{result.stdout + result.stderr}')
        
        user_id = json.loads(result.stdout)['result']['id']
        model_data['user_id'] = user_id
        
        # login user #

        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        login_user_cmd = base_cmd + ['auth', 'login-user', 'run', json.dumps(login_data), '--show', '--no-session']
        result = subprocess.run(login_user_cmd, capture_output=True, text=True, env=env, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f'Error logging in user for pagination seeding:\n{result.stdout + result.stderr}')
        
        access_token = json.loads(result.stdout)['result']['access_token']

        env['MAPP_CLI_ACCESS_TOKEN'] = access_token
        
    seed_cmd.append(json.dumps(model_data))

    return run_cmd(seed_cmd, env)

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

def request(ctx:dict, method:str, endpoint:str, request_body:Optional[dict]=None, decode_json=True) -> tuple[int, dict]:
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
    
    if decode_json:
        try:
            response_data = json.loads(body)
            return status, response_data
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Invalid JSON from {method} {endpoint}, resp length: {len(body)}: {body}')
    else:
        return status, body

def env_to_string(env:dict) -> str:
    out = ''
    for key, value in env.items():
        if ' ' in value:
            out += f'{key}="{value}"\n'
        else:
            out += f'{key}={value}\n'
    return out

def login_cached_user(cmd:list[str], ctx:dict, user_name:str, email:str, password:str='testpass123') -> dict:
    """Login to a cached user and return user data with env context"""
    login_params = {'email': email, 'password': password}
    login_cmd = cmd + ['auth', 'login-user', 'run', json.dumps(login_params), '--show', '--no-session']
    result = subprocess.run(login_cmd, capture_output=True, text=True, env=ctx, timeout=10)
    
    if result.returncode != 0:
        raise RuntimeError(f'Error logging in cached user {user_name}:\n{result.stdout + result.stderr}')
    
    login_response = json.loads(result.stdout)['result']
    access_token = login_response['access_token']
    
    # Decode JWT token to get user_id (without verification since we generated it locally)
    # Signature verification is disabled because:
    # 1. This is for test purposes only with locally generated tokens
    # 2. We just need to extract the user_id from the payload
    # 3. The token was just created by our own auth system
    try:
        token_payload = jwt.decode(access_token, options={'verify_signature': False})
        user_id = token_payload['sub']
    except (jwt.DecodeError, jwt.InvalidTokenError, KeyError) as e:
        raise RuntimeError(f'Error decoding access token for cached user {user_name}: {e}')
    
    user_data = {
        'id': user_id,
        'name': user_name,
        'email': email,
        'password': password,
        'password_confirm': password
    }
    
    user_env = ctx.copy()
    user_env['MAPP_CLI_ACCESS_TOKEN'] = access_token
    user_env['Authorization'] = f'Bearer {access_token}'
    
    return {'user': user_data, 'env': user_env}


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
    crud_users = []
    crud_ctx = {}

    pagination_db_file = Path(f'{test_dir}/test_pagination_db.sqlite3')
    pagination_envfile = Path(f'{test_dir}/pagination.env')
    pagination_user = {}
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

        crud_fs_path = Path(cls.test_dir) / 'crud_file_system'

        # delete old files #
    
        if not cls.use_cache:
            shutil.rmtree(cls.test_dir, ignore_errors=True)
        else:
            # the crud environment is always recreated
            # so we need to wipe this dir always
            shutil.rmtree(crud_fs_path, ignore_errors=True)

        os.makedirs(cls.test_dir, exist_ok=True)

        # Always delete crud DB to avoid max models exceeded errors with cached data
        # Only cache the expensive pagination DB
        if cls.crud_db_file.exists():
            cls.crud_db_file.unlink()
        
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
        crud_env['MAPP_FILE_SYSTEM_REPO'] = str(crud_fs_path.resolve())
        crud_env['MAPP_SERVER_DEVELOPMENT_MODE'] = 'true'

        try:
            del crud_env['DEBUG_DELAY']
        except KeyError:
            pass

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
        pagination_env['MAPP_FILE_SYSTEM_REPO'] = str((Path(cls.test_dir) / 'pagination_file_system').resolve())
        try:
            del pagination_env['DEBUG_DELAY']
        except KeyError:
            pass

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

        print('  :: Creating tables in test dbs ::')

        # create crud tables #

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
        
        # create crud users (always fresh since crud DB is recreated each time) #

        if cls.spec['project']['use_builtin_modules']:
            crud_users = ['alice', 'bob', 'charlie', 'david', 'evelyn']
            print('  :: Creating crud users ::')
            for user_name in crud_users:

                # create #

                user_data = {
                    'name': user_name,
                    'email': f'{user_name}@example.com',
                    'password': 'testpass123',
                    'password_confirm': 'testpass123'
                }

                create_cmd = cls.cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
                result = subprocess.run(create_cmd, capture_output=True, text=True, env=cls.crud_ctx)
                if result.returncode != 0:
                    raise RuntimeError(f'Error creating crud user {user_name}:\n{result.stdout + result.stderr}')
                
                user_id = json.loads(result.stdout)['result']['id']
                user_data['id'] = user_id
                
                # login #

                login_params = {'email': user_data['email'], 'password': 'testpass123'}
                login_cmd = cls.cmd + ['auth', 'login-user', 'run', json.dumps(login_params), '--show', '--no-session']
                result = subprocess.run(login_cmd, capture_output=True, text=True, env=cls.crud_ctx)

                # confirm and store #

                if result.returncode != 0:
                    raise RuntimeError(f'Error logging in crud user {user_name}:\n{result.stdout + result.stderr}')
                else:
                    access_token = json.loads(result.stdout)['result']['access_token']
                    user_env = cls.crud_ctx.copy()
                    user_env['MAPP_CLI_ACCESS_TOKEN'] = access_token
                    user_env['Authorization'] = f'Bearer {access_token}'
                    cls.crud_users.append({'user': user_data, 'env': user_env})

        # setup tables in test dbs #

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
                    
        # still need to use create-tables command because hidden models cannot be created individually #

        pagination_create_tables_cmd = cls.cmd + ['create-tables']
        pagination_result = subprocess.run(pagination_create_tables_cmd, capture_output=True, text=True, env=cls.pagination_ctx)
        if pagination_result.returncode != 0:
            raise RuntimeError(f'Error creating tables for pagination db: {pagination_result.stdout + pagination_result.stderr}')
        
        # seed pagination db #

        if cls.use_cache and pagination_db_exists:
            print('  :: Using cached pagination db ::')
            
            # login to cached pagination user #
            
            if cls.spec['project']['use_builtin_modules']:
                print('  :: Logging in to cached pagination user ::')
                try:
                    cls.pagination_user = login_cached_user(
                        cls.cmd, 
                        cls.pagination_ctx, 
                        'pagination_tester', 
                        'pagination_tester@example.com'
                    )
                except RuntimeError as e:
                    print(f'  :: Could not login to cached pagination user, will recreate: {e} ::')
                    # fall through to else block to recreate pagination db
                    cls.use_cache = False  # disable cache for pagination db
        
        if not cls.use_cache or not pagination_db_exists:
            print(f'  :: Seeding pagination db ::')
            seed_jobs = []
            for module in cls.spec['modules'].values():
                module_name_kebab = module['name']['kebab_case']

                for model in module['models'].values():
                    if model['hidden'] is True:
                        continue

                    if model['auth']['max_models_per_user'] == 0:
                        continue

                    model_name_kebab = model['name']['kebab_case']

                    path = f'{module_name_kebab}.{model_name_kebab}'

                    require_auth = model['auth']['require_login']

                    for index in range(cls.pagination_total_models):
                        example_model = example_from_model(model, index=0)
                        seed_cmd = cls.cmd + [module_name_kebab, model_name_kebab, 'db', 'create']
                        unique_id = f'{path}.{index}'
                        seed_jobs.append((unique_id, cls.cmd, seed_cmd, cls.pagination_ctx, require_auth, example_model))

            results = cls.pool.starmap(seed_pagination_item, seed_jobs)

            for (cmd_args, code, stdout, stderr) in results:
                if code != 0:
                    raise RuntimeError(f':: ERROR seeding table for pagination db :: COMMAND :: {" ".join(cmd_args)} :: OUTPUT :: {stdout + stderr}')
        
            # create pagination user #

            if cls.spec['project']['use_builtin_modules']:
                print('  :: Creating pagination test user ::')

                user_data = {
                    'name': 'pagination_tester',
                    'email': 'pagination_tester@example.com',
                    'password': 'testpass123',
                    'password_confirm': 'testpass123'
                }

                create_cmd = cls.cmd + ['auth', 'create-user', 'run', json.dumps(user_data)]
                create_result = subprocess.run(create_cmd, capture_output=True, text=True, env=cls.pagination_ctx)
                if create_result.returncode != 0:
                    raise RuntimeError(f'Error creating pagination test user: {create_result.stdout + create_result.stderr}')
                
                user_id = json.loads(create_result.stdout)['result']['id']
                user_data['id'] = user_id
                
                login_params = {'email': user_data['email'], 'password': 'testpass123'}
                login_cmd = cls.cmd + ['auth', 'login-user', 'run', json.dumps(login_params), '--show', '--no-session']
                login_result = subprocess.run(login_cmd, capture_output=True, text=True, env=cls.pagination_ctx)
                if login_result.returncode != 0:
                    raise RuntimeError(f'Error logging in pagination test user: {login_result.stdout + login_result.stderr}')
                
                access_token = json.loads(login_result.stdout)['result']['access_token']
                user_env = cls.pagination_ctx.copy()
                user_env['MAPP_CLI_ACCESS_TOKEN'] = access_token
                user_env['Authorization'] = f'Bearer {access_token}'
                cls.pagination_user = {'user': user_data, 'env': user_env}

        # delete server logs #

        for log_file in glob.glob(f'{cls.test_dir}/test_server_*.log'):
            try:
                Path(log_file).unlink()
            except FileNotFoundError:
                pass

        # create server configs #

        crud_server_start_cmd = cls.cmd + ['server']
        pagination_server_start_cmd = cls.cmd + ['server']
        cls.server_status_commands = []

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

            crud_server_start_cmd = ['./server.sh', 'start', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config, '--log-file', cls.crud_log_file]
            pagination_server_start_cmd = ['./server.sh', 'start', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config, '--log-file', cls.pagination_log_file]

            cls.crud_server_stop_cmd = ['./server.sh', 'stop', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config]
            cls.pagination_server_stop_cmd = ['./server.sh', 'stop', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config]

            cls.server_status_commands.append(['./server.sh', 'status', '--pid-file', cls.crud_pidfile, '--config', cls.crud_uwsgi_config])
            cls.server_status_commands.append(['./server.sh', 'status', '--pid-file', cls.pagination_pidfile, '--config', cls.pagination_uwsgi_config])

            with open(cls.crud_uwsgi_config, 'w') as f:
                crud_uwsgi_config = re.sub(port_pattern, f'http: :{crud_port}', uwsgi_config)
                crud_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.crud_pidfile}', crud_uwsgi_config)
                crud_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.crud_stats_socket}', crud_uwsgi_config)
                f.write(crud_uwsgi_config)
            
            with open(cls.pagination_uwsgi_config, 'w') as f:
                pagination_uwsgi_config = re.sub(port_pattern, f'http: :{pagination_port}', uwsgi_config)
                pagination_uwsgi_config = re.sub(pid_file_pattern, f'safe-pidfile: {cls.pagination_pidfile}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(stats_pattern, f'stats: {cls.pagination_stats_socket}', pagination_uwsgi_config)
                pagination_uwsgi_config = re.sub(logto_pattern, f'logto: {cls.pagination_log_file}', pagination_uwsgi_config)
                f.write(pagination_uwsgi_config)

        # confirm servers are stopped from previous tests #

        print('  :: Confirming no server processes are running ::')
        crud_result = subprocess.run(cls.crud_server_stop_cmd, env=cls.crud_ctx, capture_output=True, text=True, timeout=10)
        pagination_result = subprocess.run(cls.pagination_server_stop_cmd, env=cls.pagination_ctx, capture_output=True, text=True, timeout=10)
        
        # start servers #

        print('  :: Starting server processes ::')

        print('    :: ', ' '.join(crud_server_start_cmd))
        crud_result = subprocess.run(crud_server_start_cmd, env=cls.crud_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if crud_result.returncode != 0:
            raise RuntimeError(f'Error starting CRUD server: {crud_result.stdout + crud_result.stderr}')

        print('    :: ', ' '.join(pagination_server_start_cmd))
        pagination_result = subprocess.run(pagination_server_start_cmd, env=cls.pagination_ctx, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if pagination_result.returncode != 0:
            raise RuntimeError(f'Error starting pagination server: {pagination_result.stdout + pagination_result.stderr}')

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
                subprocess.run(cls.crud_server_stop_cmd, env=cls.crud_ctx, check=True, capture_output=True, timeout=15)
                subprocess.run(cls.pagination_server_stop_cmd, env=cls.pagination_ctx, check=True, capture_output=True, timeout=15)
            except subprocess.TimeoutExpired:
                print('    :: Timeout expired while stopping servers ::')
            except subprocess.CalledProcessError as e:
                print(f'    :: Error stopping servers: {e} :: {e.output} :: {e.stderr} ::')
        
        print(':: Teardown complete ::')

    def _run_cmd(self, cmd:list[str], expected_code=0, env:Optional[dict[str, str]] = None) -> subprocess.CompletedProcess:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        msg = f'expected {expected_code} got {result.returncode} for command "{' '.join(cmd)}" output: {result.stdout + result.stderr}'
        self.assertEqual(result.returncode, expected_code, msg)
        return result
    
    def _check_servers_running(self):
        error = 0
        for cmd in self.server_status_commands:
            # call via subprocess and check stdout for text RUNNING
            result = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy(), timeout=10)
            if result.returncode != 0 or 'RUNNING' not in result.stdout:
                print(f':: ERROR: Server process not running for command {" ".join(cmd)} :: Output: {result.stdout + result.stderr}')
                error += 1

        self.assertEqual(error, 0, f'{error} server processes not running')

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
        env = ctx.copy()
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
        self._test_user_auth_flow(self.crud_ctx, 'run')
    
    def test_cli_http_auth_flow(self):
        self._test_user_auth_flow(self.crud_ctx, 'http')

    def test_server_auth_flow(self):
        """
        test auth command flow via cli http command
        
        /api/auth/delete-user
            * expect error

        /api/auth/current-user
            * expect error

        /api/auth/create-user {"name": "brad", ...}
        /api/auth/login-user {"email": "...", ...}
        /api/auth/current-user
        /api/auth/logout-user {"mode": "current"}
        /api/auth/current-user
            * expect error
        /api/auth/login-user {"email": "...", ...}
        /api/auth/delete-user
        /api/auth/current-user
            * expect error
        """

        self._check_servers_running()

        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        base_ctx.update(self.crud_ctx)

        # 1. delete-user (should error)

        logged_out_delete_status, logged_out_delete_resp = request(base_ctx, 'GET', '/api/auth/delete-user')
        self.assertEqual(logged_out_delete_status, 401)
        self.assertIn('error', logged_out_delete_resp)

        # 2. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

        # 3. create-user
        create_status, create_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/create-user', 
            request_body=json.dumps({
                'name': 'alice',
                'email': 'alice-server@example.com',
                'password': 'testpass123',
                'password_confirm': 'testpass123'
            }).encode()
        )
        self.assertEqual(create_status, 200)
        self.assertIn('result', create_resp)
        self.assertIn('id', create_resp['result'])

        # 4. login-user
        login_status, login_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/login-user', 
            request_body=json.dumps({
                'email': 'alice-server@example.com',
                'password': 'testpass123'
            }).encode()
        )
        self.assertEqual(login_status, 200)
        self.assertIn('result', login_resp)
        self.assertIn('access_token', login_resp['result'])

        logged_in_ctx = base_ctx.copy()
        access_token = login_resp['result']['access_token']
        logged_in_ctx['headers']['Authorization'] = f'Bearer {access_token}'

        # 5. current-user
        current_status, current_resp = request(
            logged_in_ctx, 
            'GET', 
            '/api/auth/current-user'
        )
        self.assertEqual(current_status, 200)
        self.assertIn('email', current_resp['result'])
        self.assertEqual(current_resp['result']['email'], 'alice-server@example.com')

        # 6. logout-user (current)
        logout_status, logout_resp = request(
            logged_in_ctx, 
            'POST', 
            '/api/auth/logout-user', 
            request_body=json.dumps({'mode': 'current'}).encode()
        )
        self.assertEqual(logout_status, 200)
        self.assertIn('logged out', logout_resp['result']['message'].lower())

        # 7. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

        # 8. login-user (again)
        login_status, login_resp = request(
            base_ctx, 
            'POST', 
            '/api/auth/login-user', 
            request_body=json.dumps({
                'email': 'alice-server@example.com',
                'password': 'testpass123'
            }).encode()
        )
        self.assertEqual(login_status, 200)
        self.assertIn('access_token', login_resp['result'])

        logged_in_ctx = base_ctx.copy()
        access_token = login_resp['result']['access_token']
        logged_in_ctx['headers']['Authorization'] = f'Bearer {access_token}'

        # 9. delete-user
        delete_status, delete_resp = request(
            logged_in_ctx, 
            'GET', 
            '/api/auth/delete-user'
        )
        self.assertEqual(delete_status, 200)
        self.assertIn('deleted', delete_resp['result']['message'].lower())

        # 10. current-user (should error)
        logged_out_current_status, logged_out_current_resp = request(base_ctx, 'GET', '/api/auth/current-user')
        self.assertEqual(logged_out_current_status, 401)
        self.assertIn('error', logged_out_current_resp)

    # builtin - file system tests #

    def _test_file_system_ingest_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash.png file-system ingest-start run '{"name": "splash.png", "size": 4007485, "parts": 1, "finish": true}'

        ./run.sh file-system list-files run

        ./run.sh file-system list-parts run '{"file_id": ""}'

        ./run.sh -fo splash_copy.png file-system get-part-content run '{"file_id": "5", "part_number": 1}'
        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'
        sample_size = 4007485
        sample_checksum = 'bf3bc28ca617270e3537761e2b9c935f2ea54b6d4debe926a06e765c2bab414e'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest test does not exist')
        self.assertEqual(os.path.getsize(sample_path), sample_size, 'Sample file size does not match expected size')

        # test create #

        json_params = json.dumps({
            'name': 'splash-orig.png',
            'size': sample_size,
            'parts': 1,
            'finish': True
        })

        cmd = self.cmd + ['-fi', sample_path, 'file-system', 'ingest-start', io_type, json_params]

        # ensure logged out user cannot ingest #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # ingest with logged in user #

        create_cmd_result = self._run_cmd(cmd, env=user_env)
        create_result = json.loads(create_cmd_result.stdout)['result']
        self.assertIn('file_id', create_result, 'Ingest start result does not contain file_id')
        self.assertIn('status: good', create_result['message'], 'Ingest start result message does not indicate success')

        # confirm can list file #

        list_files_cmd = self.cmd + ['file-system', 'list-files', io_type, json.dumps({'file_id': create_result['file_id']})]
        list_files_result = self._run_cmd(list_files_cmd, env=user_env)
        list_files = json.loads(list_files_result.stdout)['result']

        self.assertEqual(len(list_files['items']), 1, 'Should be exactly 1 file in list files result')
        self.assertEqual(list_files['total'], 1, 'Total in list files result should be 1')

        file_record = list_files['items'][0]
        self.assertEqual(file_record['id'], create_result['file_id'], 'File ID in list files result does not match created file_id')
        self.assertEqual(file_record['name'], 'splash-orig.png', 'File name in list files result does not match expected name')
        self.assertEqual(file_record['size'], sample_size, 'File size in list files result does not match expected size')
        self.assertEqual(file_record['parts'], 1, 'File parts in list files result does not match expected parts')
        self.assertEqual(file_record['status'], 'good', 'File status in list files result does not indicate good status')
        self.assertEqual(file_record['user_id'], user['id'], 'File user_id in list files result does not match expected user_id')
        self.assertEqual(file_record['sha3_256'], sample_checksum, 'File sha3_256 in list files result does not match expected hash')

        # confirm can list parts #

        list_parts_cmd = self.cmd + ['file-system', 'list-parts', io_type, json.dumps({'file_id': create_result['file_id']})]
        list_parts_result = self._run_cmd(list_parts_cmd, env=user_env)
        list_parts = json.loads(list_parts_result.stdout)['result']
        self.assertEqual(len(list_parts['items']), 1, 'Should be exactly 1 part in list parts result')
        self.assertEqual(list_parts['total'], 1, 'Total in list parts result should be 1')

        part_record = list_parts['items'][0]
        self.assertEqual(part_record['file_id'], create_result['file_id'], 'Part file_id in list parts result does not match created file_id')
        self.assertEqual(part_record['part_number'], 1, 'Part number in list parts result does not match expected part number')
        self.assertEqual(part_record['size'], sample_size, 'Part size in list parts result does not match expected size')
        self.assertEqual(part_record['sha3_256'], sample_checksum, 'Part sha3_256 in list parts result does not match expected hash')
        self.assertEqual(part_record['user_id'], user['id'], 'Part user_id in list parts result does not match expected user_id')

        # confirm can get part content #
        local_part_dest = os.path.join(self.test_dir, f'splash-fs-part-content-{io_type}.png')
        get_part_cmd = self.cmd + ['-fo', local_part_dest, 'file-system', 'get-part-content', io_type, json.dumps({'file_id': create_result['file_id'], 'part_number': 1})]
        get_part_output = self._run_cmd(get_part_cmd, env=user_env)
        get_part_result = json.loads(get_part_output.stdout)['result']
        self.assertTrue(get_part_result['acknowledged'], 'Get part content result not acknowledged')
        self.assertTrue(os.path.exists(local_part_dest), 'Local file for part content does not exist after get-part-content command')
        self.assertEqual(os.path.getsize(local_part_dest), sample_size, 'Local file size for part content does not match expected size')
        with open(local_part_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, 'Local file checksum for part content does not match expected checksum')

        # confirm can get file content #

        local_file_dest = os.path.join(self.test_dir, f'splash-fs-file-content-{io_type}.png')
        get_file_cmd = self.cmd + ['-fo', local_file_dest, 'file-system', 'get-file-content', io_type, json.dumps({'file_id': create_result['file_id']})]
        get_file_output = self._run_cmd(get_file_cmd, env=user_env)
        get_file_result = json.loads(get_file_output.stdout)['result']
        self.assertTrue(get_file_result['acknowledged'], 'Get file content result not acknowledged')
        self.assertTrue(os.path.exists(local_file_dest), 'Local file for file content does not exist after get-file-content command')
        self.assertEqual(os.path.getsize(local_file_dest), sample_size, 'Local file size for file content does not match expected size')
        with open(local_file_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, 'Local file checksum for file content does not match expected checksum')


    def test_cli_run_file_system_ingest_flow(self):
        self._test_file_system_ingest_flow(self.crud_ctx, 'run')

    # builtin - media tests #

    def _test_media_create_image_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash-orig.png media create-image run '{"name": "splash.png"}'
        ./run.sh --log -fi ./tests/samples/splash-low.jpg media create-image run '{"name": "splash-low.jpg"}'

        ./run.sh media list-images run

        ./run.sh media get-image run '{"image_id": "1"}'

        ./run.sh -fo splash-media-id-1.png media get-image-file-content run '{"image_id": "1"}'

        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'
        sample_size = 4007485
        sample_checksum = 'bf3bc28ca617270e3537761e2b9c935f2ea54b6d4debe926a06e765c2bab414e'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest test does not exist')
        self.assertEqual(os.path.getsize(sample_path), sample_size, 'Sample file size does not match expected size')

        # test create image #

        json_params = json.dumps({
            'name': 'splash-orig.png'
        })

        cmd = self.cmd + ['-fi', sample_path, 'media', 'create-image', io_type, json_params]

        # ensure logged out user cannot create image #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # create image with logged in user #

        create_cmd_result = self._run_cmd(cmd, env=user_env)
        create_result = json.loads(create_cmd_result.stdout)['result']
        self.assertIn('image_id', create_result, 'Create image result does not contain image_id')
        self.assertIn('file_id', create_result, 'Create image result does not contain file_id')
        self.assertIn('message', create_result, 'Create image result does not contain message')

        self.assertTrue(isinstance(create_result['image_id'], str), 'Create image result image_id is not a string')
        self.assertTrue(isinstance(create_result['file_id'], str), 'Create image result file_id is not a string')

        # get image #

        get_image_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': create_result['image_id']})]
        get_image_result = self._run_cmd(get_image_cmd, env=user_env)
        get_image = json.loads(get_image_result.stdout)['result']
        self.assertEqual(get_image['id'], create_result['image_id'], 'Get image result id does not match created image_id')
        self.assertEqual(get_image['file_id'], create_result['file_id'], 'Get image result file_id does not match created file_id')
        self.assertEqual(get_image['file_size'], sample_size, 'Get image result size does not match expected size')
        self.assertEqual(get_image['user_id'], user['id'], 'Get image result user_id does not match expected user_id')

        # list images #

        list_images_cmd_1 = self.cmd + ['media', 'list-images', io_type, json.dumps({'image_id': create_result['image_id']})]
        list_images_cmd_2 = self.cmd + ['media', 'list-images', io_type, json.dumps({'file_id': create_result['file_id'], 'user_id': user['id']})]

        list_cmds = [list_images_cmd_1, list_images_cmd_2]

        for cmd in list_cmds:

            list_images_result = self._run_cmd(cmd, env=user_env)
            list_images = json.loads(list_images_result.stdout)['result']
            self.assertEqual(len(list_images['items']), 1, 'Should be exactly 1 image in list images result')
            self.assertEqual(list_images['total'], 1, 'Total in list images result should be 1')

            image_record = list_images['items'][0]
            self.assertEqual(image_record['id'], create_result['image_id'], 'Image ID in list images result does not match created image_id')
            self.assertEqual(image_record['file_id'], create_result['file_id'], 'Image file_id in list images result does not match created file_id')
            self.assertEqual(image_record['file_size'], sample_size, 'Image size in list images result does not match expected size')
            self.assertEqual(image_record['user_id'], user['id'], 'Image user_id in list images result does not match expected user_id')

        # get file content (download image) #

        local_image_dest = os.path.join(self.test_dir, f'splash-media-media-content-{io_type}.png')
        get_image_file_cmd = self.cmd + ['-fo', local_image_dest, 'media', 'get-media-file-content', io_type, json.dumps({'image_id': create_result['image_id']})]
        get_image_file_output = self._run_cmd(get_image_file_cmd, env=user_env)
        get_image_file_result = json.loads(get_image_file_output.stdout)['result']
        self.assertTrue(get_image_file_result['acknowledged'], 'Get media file content result not acknowledged')
        self.assertTrue(os.path.exists(local_image_dest), 'Local file for media content does not exist after get-media-file-content command')
        self.assertEqual(os.path.getsize(local_image_dest), sample_size, 'Local file size for media content does not match expected size')
        with open(local_image_dest, 'rb') as f:
            local_checksum = hashlib.sha3_256(f.read()).hexdigest()
        self.assertEqual(local_checksum, sample_checksum, 'Local file checksum for media content does not match expected checksum')

    def test_cli_run_media_create_image_flow(self):
        self._test_media_create_image_flow(self.crud_ctx, 'run')

    def test_cli_http_media_create_image_flow(self):
        self._test_media_create_image_flow(self.crud_ctx, 'http')

    def _test_media_ingest_master_image_flow(self, ctx:dict, io_type:str):
        """
        ./run.sh --log -fi ./tests/samples/splash-orig.png media ingest-master-image run '{"name": "splash-orig.png"}'
        """

        #
        # init
        #

        logged_out_ctx = self.crud_ctx.copy()
        user = self.crud_users[0]['user']
        user_env = self.crud_users[0]['env']

        sample_path = 'tests/samples/splash-orig.png'

        self.assertTrue(os.path.exists(sample_path), 'Sample file for ingest master image test does not exist')

        json_params = json.dumps({
            'name': 'splash-orig.png',
            'thumbnail_max_size': 200
        })

        cmd = self.cmd + ['-fi', sample_path, 'media', 'ingest-master-image', io_type, json_params]

        # ensure logged out user cannot ingest master image #

        self._run_cmd(cmd, env=logged_out_ctx, expected_code=1)

        # ingest master image with logged in user #

        result_output = self._run_cmd(cmd, env=user_env)
        result = json.loads(result_output.stdout)['result']

        self.assertIn('master_image_id', result, 'Ingest master image result does not contain master_image_id')
        self.assertIn('original_image_id', result, 'Ingest master image result does not contain original_image_id')
        self.assertIn('web_image_id', result, 'Ingest master image result does not contain web_image_id')
        self.assertIn('thumbnail_image_id', result, 'Ingest master image result does not contain thumbnail_image_id')
        self.assertIn('message', result, 'Ingest master image result does not contain message')

        self.assertTrue(isinstance(result['master_image_id'], str), 'master_image_id is not a string')
        self.assertTrue(isinstance(result['original_image_id'], str), 'original_image_id is not a string')
        self.assertTrue(isinstance(result['web_image_id'], str), 'web_image_id is not a string')
        self.assertTrue(isinstance(result['thumbnail_image_id'], str), 'thumbnail_image_id is not a string')

        # verify three distinct image records were created #

        ids = [result['original_image_id'], result['web_image_id'], result['thumbnail_image_id']]
        self.assertEqual(len(set(ids)), 3, 'Expected 3 distinct image IDs for original, web, and thumbnail')

        # verify thumbnail is smaller than original #

        get_original_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': result['original_image_id']})]
        get_thumb_cmd = self.cmd + ['media', 'get-image', io_type, json.dumps({'image_id': result['thumbnail_image_id']})]

        original_output = self._run_cmd(get_original_cmd, env=user_env)
        original_image = json.loads(original_output.stdout)['result']

        thumb_output = self._run_cmd(get_thumb_cmd, env=user_env)
        thumb_image = json.loads(thumb_output.stdout)['result']

        self.assertLessEqual(thumb_image['width'], 200, 'Thumbnail width should not exceed thumbnail_max_size')
        self.assertLessEqual(thumb_image['height'], 200, 'Thumbnail height should not exceed thumbnail_max_size')
        self.assertGreater(original_image['width'], thumb_image['width'], 'Original should be wider than thumbnail')

        # get master image record #

        get_master_cmd = self.cmd + ['media', 'get-master-image', io_type, json.dumps({'master_image_id': result['master_image_id']})]

        master_output = self._run_cmd(get_master_cmd, env=user_env)
        master_image = json.loads(master_output.stdout)['result']

        self.assertIn('id', master_image, 'get_master_image result does not contain id')
        self.assertIn('original_image_id', master_image, 'get_master_image result does not contain original_image_id')
        self.assertIn('web_image_id', master_image, 'get_master_image result does not contain web_image_id')
        self.assertIn('thumbnail_image_id', master_image, 'get_master_image result does not contain thumbnail_image_id')
        self.assertIn('user_id', master_image, 'get_master_image result does not contain user_id')
        self.assertIn('created_at', master_image, 'get_master_image result does not contain created_at')

        self.assertEqual(master_image['id'], result['master_image_id'], 'Master image ID does not match')
        self.assertEqual(master_image['original_image_id'], result['original_image_id'], 'original_image_id does not match')
        self.assertEqual(master_image['web_image_id'], result['web_image_id'], 'web_image_id does not match')
        self.assertEqual(master_image['thumbnail_image_id'], result['thumbnail_image_id'], 'thumbnail_image_id does not match')

        # ensure logged out user cannot get master image #

        self._run_cmd(get_master_cmd, env=logged_out_ctx, expected_code=1)

        # list master images #

        list_master_cmd = self.cmd + ['media', 'list-master-images', io_type, json.dumps({'offset': 0, 'size': 50, 'master_image_id': '-1', 'user_id': '-1'})]

        list_output = self._run_cmd(list_master_cmd, env=user_env)
        list_result = json.loads(list_output.stdout)['result']

        self.assertIn('items', list_result, 'list_master_images result does not contain items')
        self.assertIn('total', list_result, 'list_master_images result does not contain total')
        self.assertGreaterEqual(list_result['total'], 1, 'Expected at least one master image in list')
        self.assertGreaterEqual(len(list_result['items']), 1, 'Expected at least one master image item in list')

        # filter by master_image_id #

        list_by_id_cmd = self.cmd + ['media', 'list-master-images', io_type, json.dumps({'offset': 0, 'size': 50, 'master_image_id': result['master_image_id'], 'user_id': '-1'})]

        list_by_id_output = self._run_cmd(list_by_id_cmd, env=user_env)
        list_by_id_result = json.loads(list_by_id_output.stdout)['result']

        self.assertEqual(list_by_id_result['total'], 1, 'Expected exactly one master image when filtering by master_image_id')
        self.assertEqual(list_by_id_result['items'][0]['id'], result['master_image_id'], 'Filtered master image ID does not match')

        # ensure logged out user cannot list master images #

        self._run_cmd(list_master_cmd, env=logged_out_ctx, expected_code=1)

        # get master image file content (download original image via master_image_id) #

        local_master_content_dest = os.path.join(self.test_dir, f'splash-master-content-{io_type}.png')
        get_master_content_cmd = self.cmd + ['-fo', local_master_content_dest, 'media', 'get-media-file-content', io_type, json.dumps({'master_image_id': result['master_image_id']})]

        get_master_content_output = self._run_cmd(get_master_content_cmd, env=user_env)
        get_master_content_result = json.loads(get_master_content_output.stdout)['result']
        self.assertTrue(get_master_content_result['acknowledged'], 'Get media file content via master_image_id not acknowledged')
        self.assertTrue(os.path.exists(local_master_content_dest), 'Local file for master image content does not exist after get-media-file-content command')

        # ensure both image_id and master_image_id together throws an error #

        get_both_cmd = self.cmd + ['media', 'get-media-file-content', io_type, json.dumps({'image_id': result['original_image_id'], 'master_image_id': result['master_image_id']})]
        self._run_cmd(get_both_cmd, env=user_env, expected_code=1)

        # ensure neither image_id nor master_image_id throws an error #

        get_neither_cmd = self.cmd + ['media', 'get-media-file-content', io_type, json.dumps({})]
        self._run_cmd(get_neither_cmd, env=user_env, expected_code=1)

    def test_cli_run_media_ingest_master_image_flow(self):
        self._test_media_ingest_master_image_flow(self.crud_ctx, 'run')

    def test_cli_http_media_ingest_master_image_flow(self):
        self._test_media_ingest_master_image_flow(self.crud_ctx, 'http')

    # crud tests #

    def _test_cli_crud_commands(self, command_type:str, user_index:int):

        logged_out_ctx = self.crud_ctx.copy()
        create_user = self.crud_users[user_index]['user']
        create_user_env = self.crud_users[user_index]['env']
        other_user = self.crud_users[0]['user']
        other_user_env = self.crud_users[0]['env']
        self.assertNotEqual(user_index, 0, 'user_index must not be 0 to ensure different users for testing')

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model_name, model in module['models'].items():

                hidden = model['hidden']
                require_login = model['auth']['require_login']
                model_name_kebab = model['name']['kebab_case']
                max_models = model['auth']['max_models_per_user']
                model_db_args = self.cmd + [module_name_kebab, model_name_kebab, command_type]

                if require_login:
                    ctx = create_user_env
                else:
                    ctx = self.crud_ctx

                # create #

                example_to_create = example_from_model(model)
                create_args = model_db_args + ['create', json.dumps(example_to_create)]
                created_model_id = '1'

                if hidden:
                    self._run_cmd(create_args, env=ctx, expected_code=2)
                    
                else:
                    if require_login:
                        self._run_cmd(create_args, env=logged_out_ctx, expected_code=1)
                    
                    num_to_create = 1 if max_models < 0 else max_models

                    for n in range(num_to_create):

                        result = self._run_cmd(create_args, env=ctx)

                        created_model = json.loads(result.stdout)

                        created_model_id = created_model.pop('id')  # remove id for comparison
                        if require_login:
                            example_to_create['user_id'] = create_user['id']
                        
                        self.assertEqual(created_model, example_to_create, f'Created {model_name} does not match example data {n=}')

                    if max_models >= 0:
                        # try to create one more than allowed
                        self._run_cmd(create_args, env=ctx, expected_code=1)

                    if max_models == 0:
                        continue  # skip rest of tests for this model


                # read #

                read_args = model_db_args + ['read', str(created_model_id)]

                if hidden:
                    self._run_cmd(read_args, env=ctx, expected_code=2)
                    read_model_id = None
                else:
                    if require_login:
                        self._run_cmd(read_args, env=logged_out_ctx, expected_code=1)

                    result = self._run_cmd(read_args, env=ctx)
                    read_model = json.loads(result.stdout)
                    read_model_id = read_model.pop('id')
                    self.assertEqual(read_model, example_to_create, f'Read {model_name} does not match example data')
                    self.assertEqual(read_model_id, created_model_id, f'Read {model_name} ID does not match created ID')

                    if require_login:
                        self.assertIsNotNone(read_model['user_id'], f'Read {model_name} user_id is None')
                        self.assertEqual(read_model['user_id'], create_user['id'], f'Read {model_name} ID does not match created ID')

                # update #

                try:
                    updated_example = example_from_model(model, index=1)
                except ValueError as e:
                    raise ValueError(f'Need at least 2 examples for update testing: {e}')
                
                if require_login:
                    updated_example['user_id'] = create_user['id']
                
                update_args = model_db_args + ['update', created_model_id, json.dumps(updated_example)]
            
                if hidden:
                    result = self._run_cmd(update_args, env=ctx, expected_code=2)
                    updated_model_id = '1'
                else:
                    if require_login:
                        self._run_cmd(update_args, env=logged_out_ctx, expected_code=1)
                        self._run_cmd(update_args, env=other_user_env, expected_code=1)

                    result = self._run_cmd(update_args, env=ctx)
                    updated_model = json.loads(result.stdout)
                    updated_model_id = updated_model.pop('id')
                    self.assertEqual(updated_model, updated_example, f'Updated {model_name} does not match updated example data')
                    self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} ID does not match created ID')

                    if require_login:
                        self.assertIsNotNone(updated_model['user_id'], f'Updated {model_name} user_id is None')
                        self.assertEqual(updated_model['user_id'], create_user['id'], f'Updated {model_name} ID does not match created ID')

                # delete #

                delete_args = model_db_args + ['delete', str(created_model_id)]

                if hidden:
                    result = self._run_cmd(delete_args, env=ctx, expected_code=2)
                else:
                    if require_login:
                        self._run_cmd(delete_args, env=logged_out_ctx, expected_code=1)
                        self._run_cmd(delete_args, env=other_user_env, expected_code=1)

                    result = self._run_cmd(delete_args, env=ctx)
                    delete_output = json.loads(result.stdout)
                    self.assertEqual(delete_output['acknowledged'], True, f'Delete {model_name} ID did not return acknowledgement')
                    expected_delete_msg = f'{model["name"]["snake_case"]} {created_model_id} has been deleted'
                    self.assertTrue(delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message')

                    # confirm delete is idempotent #

                    result = self._run_cmd(model_db_args + ['delete', str(created_model_id)], env=ctx)
                    delete_output = json.loads(result.stdout)
                    self.assertTrue(delete_output['message'].startswith(expected_delete_msg), f'Delete {model_name} ID did not return correct message')

                # read after delete #

                if not hidden:
                    result = self._run_cmd(model_db_args + ['read', str(created_model_id)], expected_code=1, env=ctx)
                    try:
                        read_output_err = json.loads(result.stdout)['error']
                        self.assertEqual(read_output_err['code'], 'NOT_FOUND', f'Read after delete for {model_name} did not return NOT_FOUND code for id {created_model_id}')
                        self.assertEqual(read_output_err['message'], f'{model["name"]["snake_case"]} {created_model_id} not found', f'Read after delete for {model_name} did not return correct message for id {created_model_id}')
                    except KeyError as e:
                        raise RuntimeError(f'KeyError {e} while reading after delete for {model_name} id {created_model_id}: {result.stdout + result.stderr}')
                    except json.JSONDecodeError as e:
                        raise RuntimeError(f'JSONDecodeError {e} while reading after delete for {model_name} id {created_model_id}: {result.stdout + result.stderr}')
                    
                # test data isolation between users #

                if require_login:
                    self.assertIsNotNone(create_user['id'], 'Create user ID is None, test setup error')
                    self.assertIsNotNone(other_user['id'], 'Other user ID is None, test setup error')
                    self.assertNotEqual(create_user['id'], other_user['id'], 'Alice and Bob users have the same ID, test setup error')
                    self.assertNotEqual(create_user_env['MAPP_CLI_ACCESS_TOKEN'], other_user_env['MAPP_CLI_ACCESS_TOKEN'], 'Alice and Bob have the same access token, test setup error')
 
    def test_cli_db_crud(self):
        self._test_cli_crud_commands('db', 1)

    def test_cli_http_crud(self):
        self._test_cli_crud_commands('http', 2)

    def test_server_crud_endpoints(self):

        self._check_servers_running()
        
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.crud_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        logged_out_ctx.update(self.crud_ctx)

        alice_user = self.crud_users[0]['user']
        alice_ctx = deepcopy(base_ctx)
        alice_ctx['headers']['Authorization'] = self.crud_users[0]['env']['Authorization']
        bob_user = self.crud_users[1]['user']
        bob_ctx = deepcopy(base_ctx)
        bob_ctx['headers']['Authorization'] = self.crud_users[1]['env']['Authorization']
        
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():

                hidden = model['hidden']
                require_login = model['auth']['require_login']
                model_name_kebab = model['name']['kebab_case']
                max_models = model['auth']['max_models_per_user']

                #
                # create
                #

                example_to_create = example_from_model(model)
                create_args = [
                    'POST',
                    f'/api/{module_name_kebab}/{model_name_kebab}',
                    json.dumps(example_to_create).encode()
                ]

                if require_login and not hidden:
                    created_status, data = request(
                        logged_out_ctx,
                        *create_args
                    )
                    self.assertEqual(created_status, 401, f'Create {model_name} without login did not return 401 Unauthorized, response: {data}')
                    ctx = alice_ctx
                else:
                    ctx = base_ctx

                # send request #

                num_to_create = 1 if max_models < 0 else max_models

                created_model_id = '1'

                for n in range(num_to_create):

                    created_status, created_model = request(
                        ctx,
                        *create_args
                    )

                    # confirm response #

                    if hidden:
                        self.assertEqual(created_status, 404, f'Create hidden {model_name} did not return 404 Not Found, {n=} response: {created_model}')
                        
                    else:
                        self.assertEqual(created_status, 200, f'Create {model_name} did not return status 200 OK, {n=} response: {created_model}')
                        created_model_id = created_model.pop('id')  # remove id for comparison
                        if require_login:
                            example_to_create['user_id'] = alice_user['id']

                        self.assertEqual(created_model, example_to_create, f'Created {model_name} (id: {created_model_id} n: {n}) does not match example data')
                
                if max_models >= 0:
                    max_created_status, max_created_model = request(
                        ctx,
                        *create_args
                    )
                    self.assertEqual(max_created_status, 400, f'Create {model_name} beyond max_models_per_user did not return 400 Bad Request, response: {max_created_model}')

                if max_models == 0:
                    continue  # skip rest of tests for this model


                #
                # read
                #

                if require_login and not hidden:
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
                
                if require_login and not hidden:
                    updated_example['user_id'] = alice_user['id']

                    # logged out cannot update #
                    
                    update_status, data = request(
                        logged_out_ctx,
                        'PUT',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        json.dumps(updated_example).encode()
                    )
                    self.assertEqual(update_status, 401, f'Update {model_name} without login did not return 401 Unauthorized, response: {data}')

                    # bob cannot update alice's model #

                    update_status, data = request(
                        bob_ctx,
                        'PUT',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        json.dumps(updated_example).encode()
                    )
                    self.assertEqual(update_status, 401, f'Update {model_name} by non-owner did not return 401 Unauthorized, response: {data}')

                    # read back to confirm not udpated #

                    read_status, read_model = request(
                        ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    ) 
                    self.assertEqual(read_status, 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}')
                    read_model_id = read_model.pop('id')
                    self.assertEqual(read_model, example_to_create, f'Read {model_name} id: {read_model_id} does not match example data after failed update attempt')
                
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
                    updated_model_id = '1'

                else:
                    self.assertEqual(updated_status, 200, f'Update {model_name} id: {created_model_id} did not return status 200 OK, response: {updated_model}')
                    updated_model_id = updated_model.pop('id')
                    self.assertEqual(updated_model, updated_example, f'Updated {model_name} id: {updated_model_id} does not match updated example data')
                    self.assertEqual(updated_model_id, created_model_id, f'Updated {model_name} id: {updated_model_id} does not match created id: {created_model_id}')

                #
                # delete
                #

                if require_login and not hidden:

                    # logged out cannot delete #

                    delete_status, data = request(
                        logged_out_ctx,
                        'DELETE',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.assertEqual(delete_status, 401, f'Delete {model_name} without login did not return 401 Unauthorized, response: {data}')

                    # bob cannot delete alice's model #

                    delete_status, data = request(
                        bob_ctx,
                        'DELETE',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.assertEqual(delete_status, 401, f'Delete {model_name} by non-owner did not return 401 Unauthorized, response: {data}')

                    # read back to confirm not deleted #

                    read_status, read_model = request(
                        ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}/{created_model_id}',
                        None
                    )
                    self.assertEqual(read_status, 200, f'Read {model_name} id: {created_model_id} did not return status 200 OK, response: {read_model}')
                    read_model_id = read_model.pop('id')
                    self.assertEqual(read_model, updated_example, f'Read {model_name} id: {read_model_id} does not match updated example data after failed delete attempt')

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

                # confirm data isolation between users #

                self.assertNotEqual(alice_user['id'], bob_user['id'], 'Alice and Bob users have the same ID, test setup error')
                self.assertNotEqual(alice_ctx['headers']['Authorization'], bob_ctx['headers']['Authorization'], 'Alice and Bob have the same Authorization header, test setup error')

    # pagination tests #

    def _test_cli_pagination_command(self, command_type:str):

        # init tests #

        logged_out_ctx = self.pagination_ctx.copy()
        commands = []
        test_cases = []

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                model_name_kebab = model['name']['kebab_case']
                model_list_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'list']
                hidden = model['hidden']
    
                if model['auth']['require_login'] and not hidden:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=1, env=logged_out_ctx)
                    ctx = self.pagination_user['env']
                else:
                    ctx = self.pagination_ctx

                if hidden is True:
                    self._run_cmd(model_list_command + ['--size=10', '--offset=0'], expected_code=2, env=self.pagination_ctx)
                    continue

                for case in self.pagination_cases:
                    size = case['size']
                    expected_pages = case['expected_pages']
                    offset = 0

                    for page in range(expected_pages):
                        commands.append((model_list_command + [f'--size={size}', f'--offset={offset}'], ctx))
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
                self.assertEqual(code, 0, f'Pagination for {model_name_kebab} page {page} returned non-zero exit code. STDOUT: {stdout} STDERR: {stderr}')
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
        
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.pagination_ctx)

        logged_out_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        logged_out_ctx.update(self.pagination_ctx)
        
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']
            for model_name, model in module['models'].items():

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                hidden = model['hidden']
                model_name_kebab = model['name']['kebab_case']

                if model['auth']['require_login'] and not hidden:
                    status, response = request(
                        logged_out_ctx,
                        'GET',
                        f'/api/{module_name_kebab}/{model_name_kebab}?size=10&offset=0',
                        None
                    )
                    self.assertEqual(status, 401, f'Pagination for {model_name_kebab} without login did not return 401 Unauthorized, response: {response}')
                    ctx = base_ctx.copy()
                    ctx['headers']['Authorization'] = self.pagination_user['env']['Authorization']
                else:
                    ctx = base_ctx

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
      
    # op tests #

    def _test_op_cli(self, command_type:str):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for op in module.get('ops', {}).values():
                op_name_kebab = op['name']['kebab_case']

                test_cases = op.get('tests', {}).get('test_cases', [])
                for n, test_case in enumerate(test_cases):
                    json_data = json.dumps(test_case['params'])
                    hidden = op['hidden']
                    args = self.cmd + [module_name_kebab, op_name_kebab, command_type, json_data]
                    if hidden:
                        self._run_cmd(args, env=self.crud_ctx, expected_code=2)
                    else:
                        result = self._run_cmd(args, env=self.crud_ctx)
                        result = json.loads(result.stdout)['result']
                        expected_result = test_case['expected_result']
                        self.assertEqual(result, expected_result, f'OP {module_name_kebab}.{op_name_kebab} output does not match expected result for index: {n}')

    def test_op_cli_run(self):
        self._test_op_cli('run')
    
    def test_op_cli_http(self):
        self._test_op_cli('http')
    
    def test_op_server_op(self):

        self._check_servers_running()

        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }

        base_ctx.update(self.crud_ctx)

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for op in module.get('ops', {}).values():
                op_name_kebab = op['name']['kebab_case']
                test_cases = op.get('tests', {}).get('test_cases', [])

                for n, test_case in enumerate(test_cases):
                    json_data = json.dumps(test_case['params']).encode()
                    hidden = op['hidden']
                    op_url = f'/api/{module_name_kebab}/{op_name_kebab}'

                    status, response = request(base_ctx, 'POST', op_url, json_data)
                    
                    if hidden:
                        self.assertEqual(status, 404, f'OP {module_name_kebab}.{op_name_kebab} hidden did not return 404 Not Found, response: {response}')
                    else:
                        self.assertEqual(status, 200, f'OP {module_name_kebab}.{op_name_kebab} did not return status 200 OK, response: {response}')
                        result = response['result']
                        expected_result = test_case['expected_result']
                        self.assertEqual(result, expected_result, f'OP {module_name_kebab}.{op_name_kebab} output does not match expected result for index: {n}')

    # validation tests #

    def _test_cli_validation_error(self, module_name_kebab:str, model:dict, command_type:str, user_index:int):
        if model['auth']['max_models_per_user'] == 0:
            return  # skip models that do not allow any data
        
        example_to_update = example_from_model(model)

        if model['hidden'] is True:
            return
        
        user_id = self.crud_users[user_index]['user']['id']
        
        if model['auth']['require_login']:
            ctx = self.crud_users[user_index]['env']
            example_to_update['user_id'] = user_id
        else:
            ctx = self.crud_ctx

        model_name_kebab = model['name']['kebab_case']

        # create model to attempt to update with invalid data #

        args = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(example_to_update)]
        result = self._run_cmd(args, env=ctx)
        update_model_id = str(json.loads(result.stdout)['id'])

        for invalid_example in model_validation_errors(model):
            model_name_kebab = model['name']['kebab_case']

            # create #

            model_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'create', json.dumps(invalid_example)]
            result = self._run_cmd(model_command, expected_code=1, env=ctx)

            error_output = json.loads(result.stdout)
            self.assertEqual(error_output['code'], 'validation_error', f'Expected validation_error code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {error_output["code"]}')
            self.assertTrue(error_output['message'].startswith('Validation Error: '), f'Expected validation_error message for {model["name"]["pascal_case"]} with invalid data {invalid_example} to start with "Validation error: ", got {error_output["message"]}')

            # update #

            model_command = self.cmd + [module_name_kebab, model_name_kebab, command_type, 'update', update_model_id, json.dumps(invalid_example)]
            result = self._run_cmd(model_command, expected_code=1, env=ctx)
            error_output = json.loads(result.stdout)
            self.assertEqual(error_output['code'], 'validation_error', f'Expected validation_error code for {model["name"]["pascal_case"]} with invalid data {invalid_example}, got {error_output["code"]}')
            self.assertTrue(error_output['message'].startswith('Validation Error: '), f'Expected validation_error message for {model["name"]["pascal_case"]} with invalid data {invalid_example} to start with "Validation error: ", got {error_output["message"]}')

        # read back original example to ensure it was not modified #

        result = self._run_cmd(self.cmd + [module_name_kebab, model_name_kebab, command_type, 'read', update_model_id], env=ctx)
        read_model = json.loads(result.stdout)
        del read_model['id']
        if model['auth']['require_login']:
            example_to_update['user_id'] = user_id
        self.assertEqual(read_model, example_to_update, f'Read {model["name"]["pascal_case"]} does not match original example data after validation error tests')

    def test_cli_db_validation_error(self):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                self._test_cli_validation_error(module_name_kebab, model, 'db', 3)

    def test_cli_http_validation_error(self):
        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():
                self._test_cli_validation_error(module_name_kebab, model, 'http', 4)

    def test_server_validation_error(self):
        self._check_servers_running()
        base_ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        base_ctx.update(self.crud_ctx)

        for module in self.spec['modules'].values():
            module_name_kebab = module['name']['kebab_case']

            for model in module['models'].values():

                if model['hidden'] is True:
                    continue

                if model['auth']['max_models_per_user'] == 0:
                    continue  # skip models that do not allow any data

                model_name_kebab = model['name']['kebab_case']

                if model['auth']['require_login']:
                    ctx = base_ctx.copy()
                    ctx['headers']['Authorization'] = self.crud_users[0]['env']['Authorization']
                else:
                    ctx = base_ctx

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
                if model['auth']['require_login']:
                    example_to_update['user_id'] = self.crud_users[0]['user']['id']
                
                self.assertEqual(read_model, example_to_update, f'Read after validation error for {model["name"]["pascal_case"]} does not match original example data')

    # other tests #

    def test_debug_responses(self):
        """
        make request to /api/debug/PlainTextResponse
            expect 200 with request body:
              This is a plain text debug response
        """

        ctx = {
            'headers': {
                'Content-Type': 'application/json',
            }
        }
        ctx.update(self.crud_ctx)

        #
        # success
        #

        # plain text response #

        status, response = request(ctx, 'GET', '/api/debug/PlainTextResponse', None, decode_json=False)
        self.assertEqual(status, 200)
        self.assertEqual(response, 'This is a plain text debug response')

        # json response #

        status, response = request(ctx, 'GET', '/api/debug/JSONResponse', None)
        self.assertEqual(status, 200)
        self.assertEqual(response, {'message': 'This is a JSON debug response'})

        #
        # error
        #

        # not found response #

        status, response = request(ctx, 'GET', '/api/debug/NotFoundError', None)
        self.assertEqual(status, 404)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'NOT_FOUND')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: NotFoundError thrown')

        # authentication error #

        status, response = request(ctx, 'GET', '/api/debug/AuthenticationError', None)
        self.assertEqual(status, 401)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'AUTHENTICATION_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: AuthenticationError thrown')

        # forbidden error #

        status, response = request(ctx, 'GET', '/api/debug/ForbiddenError', None)
        self.assertEqual(status, 403)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'FORBIDDEN_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: ForbiddenError thrown')

        # validation error #

        status, response = request(ctx, 'GET', '/api/debug/MappValidationError', None)
        self.assertEqual(status, 400)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'VALIDATION_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: MappValidationError thrown')
        field_errors = response.get('error', {}).get('field_errors', {})
        self.assertEqual(field_errors, {'field': 'example error'}, f'Unexpected field_errors content: {field_errors}')

        # request error #

        status, response = request(ctx, 'GET', '/api/debug/RequestError', None)
        self.assertEqual(status, 400)
        self.assertEqual(response.get('error', {}).get('code', '-'), 'REQUEST_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Debug: RequestError thrown')

        # exception #

        status, response = request(ctx, 'GET', '/api/debug/Exception', None)
        self.assertEqual(status, 500)
        error = response.get('error', {})
        self.assertIn('request_id', error, 'Expected request_id in error response for Exception')
        self.assertEqual(response.get('error', {}).get('code', '-'), 'INTERNAL_SERVER_ERROR')
        self.assertEqual(response.get('error', {}).get('message', ''), 'Contact support or check logs for details')

        response_str = json.dumps(response)
        self.assertNotIn('This error should not be shown to users', response_str, 'Internal error message leaked to user in Exception response')

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

def test_npm(npm_run:str, spec_path:str|Path, cli_args:list[str], host:str|None, env_file:str|None, use_cache:bool=False, app_type:str='', verbose:bool=False) -> bool:
    if cli_args is None:
        raise ValueError('args must be provided as a list of strings')
    
    # start servers

    TestMTemplateApp.spec = load_generator_spec(spec_path)
    TestMTemplateApp.cmd = cli_args
    TestMTemplateApp.host = host
    TestMTemplateApp.env_file = env_file
    TestMTemplateApp.use_cache = use_cache
    TestMTemplateApp.app_type = app_type
    TestMTemplateApp.setUpClass()
    print(':: server setup complete')

    # run npm command #

    npm_cmd = ['npm', 'run', npm_run]
    print(f':: running npm command: {" ".join(npm_cmd)}')

    test_result = False
    
    try:
        process = subprocess.Popen(npm_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # run command and forward stdout/stderr in real time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output, end='')

        # process exited
        stderr = process.stderr.read()
        if stderr:
            print(stderr, end='')

        return_code = process.poll()
        print(f':: npm command exit code {return_code}')
        if return_code == 0:
            test_result = True

    except Exception as e:
        print(f':: exception while running npm command: {e}')

    finally:
        TestMTemplateApp.tearDownClass()

    print(f'\n:: npm test result: {"PASS" if test_result else "FAIL"}\n\n')
    return test_result

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
    parser.add_argument('--npm-run', type=str, help='Start test servers, then run "npm run <arg>", ex: "--npm-run test"')

    args = parser.parse_args()

    if args.npm_run:
        test_npm(args.npm_run, args.spec, args.cmd, args.host, args.env_file, args.use_cache, args.app_type, args.verbose)

    else:
        if args.test_filter:
            # Attach filter patterns to test_spec function for access
            test_spec._test_filters = args.test_filter
        else:
            test_spec._test_filters = None

        test_spec(args.spec, args.cmd, args.host, args.env_file, args.use_cache, args.app_type, args.verbose)