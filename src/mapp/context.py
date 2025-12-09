import os
import json
import atexit
import sqlite3
import getpass

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable

from mapp.errors import MappError
from mapp.types import convert_dict_to_op_params, convert_dict_to_model, CurrentUserFunc
from mspec.core import load_mapp_spec

__all__ = [
    'DEFAULT_DB_PATH',
    'DBContext',
    'ModelRouteContext',
    'RequestContext',
    'MappContext',
    'get_context_from_env'
]

DEFAULT_DB_PATH = Path(__file__).parent / 'db.sqlite3'


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

#
# mapp context
#

@dataclass
class MappContext:
    server_port: int
    client: ClientContext
    db:DBContext
    log:Callable[[str], None]
    current_user:Optional[CurrentUserFunc]=None


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
