from sample import *
from pymongo import MongoClient

# vars :: {"mongodb://127.0.0.1:27017": "db.default_url"}

__all__ = [
    'db_init'
]

_db_client = None

def db_init(client:MongoClient=None) -> None:
    """
    initialize the database client.

    args ::
        client :: the client to use, if None, a new client will be created with default settings.
    
    return :: None
    """
    global _db_client
    if client is None:
        _db_client = MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=3_000)
    else:
        _db_client = client

    return _db_client


def db_client() -> MongoClient:
    """
    get the database client.

    return :: the database client.
    """
    return _db_client
