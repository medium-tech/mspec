from pymongo import MongoClient
# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case", "Sample": "module.name.camel_case"}
from sample_module import sample_module_db
# end for ::
import atexit

# vars :: {"mongodb://127.0.0.1:27017": "db.default_url", "MSpec": "project.name.camel_case"}

__all__ = [
    'create_db_context'
]

def create_db_context(client:MongoClient=None) -> dict:
    """
    initialize the database client.

    args ::
        client :: the client to use, if None, a new client will be created with default settings.
    
    return :: None
    """
    if client is None:
        client = MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=3_000)

    atexit.register(client.close)

    return {'db': {'client': client}}

class MSpecDB:

    # for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case", "Sample": "module.name.camel_case"}
    sample_module = sample_module_db
    # end for ::
