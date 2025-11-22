import os

from dataclasses import dataclass


@dataclass
class Context:
    server_port: int
    client_host: str
    db_file: str

def get_context_from_env():
    return Context(**{
        'server_port': int(os.getenv('SERVER_PORT', 8000)),
        'client_host': os.getenv('CLIENT_HOST', 'http://localhost:8000'),
        'db_file': os.getenv('DB_FILE', 'db.sqlite3')
    })
