import os
import json
import atexit
import sqlite3
import getpass

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable
from cryptography.fernet import Fernet
import base64

from mapp.errors import MappError
from mapp.types import convert_dict_to_op_params, convert_dict_to_model, CurrentAccessTokenFunc
from mspec.core import load_mapp_spec

__all__ = [
    'DEFAULT_DB_PATH',
    'DBContext',
    'ModelRouteContext',
    'RequestContext',
    'MappContext',
    'get_context_from_env'
]

MAPP_APP_PATH = Path(os.getenv('MAPP_APP_PATH', os.getcwd()))
DEFAULT_DB_PATH = Path(MAPP_APP_PATH) / 'db.sqlite3'


@dataclass
class DBContext:
    db_url: str
    connection: sqlite3.Connection
    cursor: sqlite3.Cursor
    commit: callable


@dataclass
class ClientContext:
    host: str
    headers: dict

    def set_bearer_token(self, access_token: str):
        self.headers['Authorization'] = f'Bearer {access_token}'


@dataclass
class ModelRouteContext:
    model_class: type
    model_kebab_case: str
    module_kebab_case: str
    api_instance_regex: str
    api_model_regex: str


@dataclass
class OpRouteContext:
    params_class: type
    output_class: type
    op_kebab_case: str
    module_kebab_case: str
    api_op_regex: str
    run_op: callable


@dataclass
class RequestContext:
    env: dict
    raw_req_body: bytes
    request_id: str

#
# mapp context
#

@dataclass
class MappContext:
    server_port: int
    client: ClientContext
    db:DBContext
    log:Callable[[str], None]
    current_access_token:Optional[CurrentAccessTokenFunc]=None

def get_context_from_env():

    # db_url = os.getenv('MAPP_DB_URL', f'file:{DEFAULT_DB_PATH}')
    db_url = os.environ['MAPP_DB_URL']
    db_conn = sqlite3.connect(db_url, uri=True)
    atexit.register(lambda: db_conn.close())

    client_host = os.getenv('MAPP_CLIENT_HOST', 'http://localhost:8000')

    return MappContext(
        server_port=int(os.getenv('MAPP_SERVER_PORT', 8000)),
        client=ClientContext(
            host=client_host,
            headers={},
        ),
        log=lambda msg: msg,   # passthru log
        db=DBContext(
            db_url=db_url,
            connection=db_conn,
            cursor=db_conn.cursor(),
            commit=db_conn.commit,
        )
    )

#
# mapp spec file
#

def spec_from_env() -> dict:
    spec_path = os.environ.get('MAPP_SPEC_FILE', 'mapp-spec.yaml')

    try:
        return load_mapp_spec(spec_path)
    except FileNotFoundError:
        raise MappError('SPEC_FILE_NOT_FOUND', f'Spec file not found: {spec_path}')

#
# cli
#

CLI_SESSION_FILE_PATH = os.path.join(os.path.expanduser('~'), '.mapp', 'cli_session.json')

def _get_fernet(ctx:MappContext) -> Fernet:
    key_hex = os.environ.get('MAPP_AUTH_SECRET_KEY')
    if not key_hex:
        raise MappError('NO_SECRET_KEY', 'MAPP_AUTH_SECRET_KEY not set in environment')
    try:
        key_bytes = bytes.fromhex(key_hex)
        fernet_key = base64.urlsafe_b64encode(key_bytes)
    except Exception as e:
        ctx.log(f'Error getting fernet key: {e.__class__.__name__}: {e}')
        raise MappError('INVALID_SECRET_KEY', 'MAPP_AUTH_SECRET_KEY is invalid')
    
    return Fernet(fernet_key)

def cli_load_session(ctx:MappContext) -> str | None:
    """TODO: optimize by caching the file contents in memory"""
    try:
        with open(CLI_SESSION_FILE_PATH, 'rb') as f:
            encrypted = f.read()
        cipher = _get_fernet(ctx)
        return cipher.decrypt(encrypted).decode()
    except FileNotFoundError:
        return None
    
def cli_write_session(ctx:MappContext, access_token: str):
    session_dir = os.path.dirname(CLI_SESSION_FILE_PATH)
    os.makedirs(session_dir, exist_ok=True)
    cipher = _get_fernet(ctx)
    encrypted = cipher.encrypt(access_token.encode())
    with open(CLI_SESSION_FILE_PATH, 'wb') as f:
        f.write(encrypted)

def cli_delete_session():
    try:
        os.remove(CLI_SESSION_FILE_PATH)
    except FileNotFoundError:
        pass

def get_cli_access_token(ctx: MappContext) -> str:
    
    try:
        access_token = os.environ['MAPP_CLI_ACCESS_TOKEN']
        ctx.log('Logged in via MAPP_CLI_ACCESS_TOKEN env variable.')
    except KeyError:
        access_token = cli_load_session(ctx)
        if access_token is None:
            raise MappError('NO_CLI_ACCESS_TOKEN', 'No session found, set MAPP_CLI_ACCESS_TOKEN or login via \'mapp auth login-user\'.')
        ctx.log('Logged in via local CLI session.')
    
    return access_token

def _cli_get_secure_input(spec:dict, json_str:str, interactive:bool) -> dict:

    # get json data #

    if json_str is None:
        json_data = dict()
    else:
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid JSON: {e}')
    
    # if interactive, prompt for inputs not provided #

    if interactive:

        for field in spec.values():

            name = field['name']['snake_case']

            if name not in json_data:

                if field['secure_input']:
                    user_input = getpass.getpass(f'Enter value for {name}:')
                else:
                    user_input = input(f'Enter value for {name}: ')

                json_data.update({name: user_input})

    return json_data

def cli_model_user_input(model_class:type, json_str:str, interactive:bool) -> dict:
    data = _cli_get_secure_input(model_class._model_spec['fields'], json_str, interactive)
    return convert_dict_to_model(model_class, data)

def cli_op_user_input(op_class:type, json_str:str, interactive:bool) -> dict:
    data = _cli_get_secure_input(op_class._op_spec['params'], json_str, interactive)
    return convert_dict_to_op_params(op_class, data)
