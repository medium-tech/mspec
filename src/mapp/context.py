import os
import atexit
import sqlite3

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from mapp.errors import MappError
from mspec.core import load_mapp_spec

__all__ = [
    'DEFAULT_DB_PATH',
    'DBContext',
    'RouteContext',
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
class RouteContext:
    model_class: type
    model_kebab_case: str
    module_kebab_case: str
    api_instance_regex: str
    api_model_regex: str


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
    log:callable
    current_user:Optional[callable]=None


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
