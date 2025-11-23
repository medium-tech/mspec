import os
import atexit
import sqlite3

from pathlib import Path
from dataclasses import dataclass

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
class RouteContext:
    model_class: type
    model_snake_case: str
    module_snake_case: str
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
    client_host: str
    db:DBContext
    log:callable


def get_context_from_env():

    db_url = os.getenv('MAPP_DB_URL', f'file:{DEFAULT_DB_PATH}')
    db_conn = sqlite3.connect(db_url, uri=True)
    atexit.register(lambda: db_conn.close())

    return MappContext(
        server_port=int(os.getenv('MAPP_SERVER_PORT', 8000)),
        client_host=os.getenv('MAPP_CLIENT_HOST', 'http://localhost:8000'),
        log=lambda msg: msg,   # passthru log
        db=DBContext(
            db_url=db_url,
            connection=db_conn,
            cursor=db_conn.cursor(),
            commit=db_conn.commit,
        )
    )
