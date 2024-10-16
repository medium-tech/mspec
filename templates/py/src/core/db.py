from pymongo import MongoClient
# for :: {% for module in proejct.modules %} :: {"sample": "module.snake_case", "Sample": "module.camel_case"}
from sample import sample_db
# end for ::

# vars :: {"mongodb://127.0.0.1:27017": "db.default_url", "MSpec": "project.camel_case"}

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

    return {'db': {'client': client}}

class MSpecDB:

    # for :: {% for module in proejct.modules %} :: {"sample": "module.snake_case", "Sample": "module.camel_case"}
    sample = sample_db
    # end for ::
