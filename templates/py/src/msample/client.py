import os
import urllib.request

from . data import verify, to_json

__all__ = ['create', 'read', 'update', 'delete', 'list']

host = os.environ.get('HOST', 'http://localhost:8000')
headers = {'Content-Type': 'application/json'}

def create(data:dict) -> str:
    verify(data)
    as_json = to_json(data)
    req = urllib.request.Request(f'{host}/sample', headers=headers, method='POST', data=as_json.encode())
    with urllib.request.urlopen(req) as res:
        return res.read()

def read():
    pass

def update():
    pass

def delete():
    pass

def list():
    pass
