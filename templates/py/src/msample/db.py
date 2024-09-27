from . data import *

__all__ = ['db_create', 'db_read', 'db_update', 'db_delete', 'db_list']

def db_create(data:dict) -> str:
    verify(data)
    as_json = to_json(data)

def db_read() -> dict:
    pass

def db_update() -> None:
    pass

def db_delete() -> None:
    pass

def db_list(offset:int=0, limit:int=25) -> list[dict]:
    pass
