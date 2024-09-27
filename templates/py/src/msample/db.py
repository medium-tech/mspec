from msample import to_json, verify

__all__ = ['db_create', 'db_read', 'db_update', 'db_delete', 'db_list']

def db_create(data:dict) -> str:
    json_str = to_json(verify(data))

def db_read(id:str) -> dict:
    pass

def db_update(id:str, data:dict) -> None:
    pass

def db_delete(id:str) -> None:
    pass

def db_list(offset:int=0, limit:int=25) -> list[dict]:
    pass
