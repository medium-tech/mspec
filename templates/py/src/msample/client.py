import os
import urllib.request

from msample import verify, to_json

__all__ = ['client_create', 'client_read', 'client_update', 'client_delete', 'client_list']

host = os.environ.get('HOST', 'http://localhost:8000')
headers = {'Content-Type': 'application/json'}

def client_create(data:dict) -> str:
    as_json = to_json(verify(data))
    req = urllib.request.Request(f'{host}/sample', headers=headers, method='POST', data=as_json.encode())
    with urllib.request.urlopen(req) as res:
        return res.read()

def client_read(id:str):
    pass

def client_update(id:str, data:dict):
    pass

def client_delete(id:str):
    pass

def client_list(offset:int=0, limit:int=25):
    pass
