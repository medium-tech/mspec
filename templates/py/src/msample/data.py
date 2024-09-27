import json

__all__ = ['verify', 'to_json', 'from_json']

def verify(data:dict):
    pass

def to_json(data:dict, **kwargs) -> str:
    return json.dumps(data, **kwargs)

def from_json(data:str) -> dict:
    return json.loads(data)
