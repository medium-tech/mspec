import os
import atexit
import sqlite3

from pathlib import Path
from dataclasses import dataclass


DEFAULT_DB_PATH = Path(__file__).parent / 'db.sqlite3'


@dataclass
class DBContext:
    db_url: str
    connection: sqlite3.Connection
    cursor: sqlite3.Cursor
    commit: callable


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
