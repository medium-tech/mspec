import os

from mapp.types import new_model_class, convert_data_to_model
from mspec.util import generate_names

ContextModelSpec = {
    'name': generate_names('context model'),
    'fields': {
        'server_port': {
            'name': generate_names('server port'),
            'type': 'int',
            'required': True,
            'examples': [8000]
        },
        'client_host': {
            'name': generate_names('client host'),
            'type': 'str',
            'required': True,
            'examples': ['http://localhost:8000']
        },
        'db_file': {
            'name': generate_names('db file'),
            'type': 'str',
            'required': True,
            'examples': ['db.sqlite3']
        }
    }
}

ContextModel = new_model_class(ContextModelSpec)


def get_context_from_env():
    env_data = {
        'server_port': int(os.getenv('SERVER_PORT', 8000)),
        'client_host': os.getenv('CLIENT_HOST', 'http://localhost:8000'),
        'db_file': os.getenv('DB_FILE', 'db.sqlite3')
    }
    return convert_data_to_model(ContextModel, env_data)
