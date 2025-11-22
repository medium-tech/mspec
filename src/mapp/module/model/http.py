import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

from mapp.context import MappContext
from mapp.errors import *
from mapp.types import from_json, to_json, list_from_json


__all__ = [
    'http_model_create',
    'http_model_read',
    'http_model_update',
    'http_model_delete',
    'http_model_list'
]


def http_model_create(ctx: MappContext, model_class:type, model:object) -> object:

    # init #

    module_kebab = model_class._model_spec['module']['kebab_case']
    model_kebab = model_class._model_spec['name']['kebab_case']

    url = f'{ctx.host}/api/{module_kebab}/{model_kebab}'
    request_body = to_json(model).encode()

    # send request #

    try:
        request = Request(url, headers=ctx.headers, method='POST', data=request_body)
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return from_json(model_class, response_body)
        
    except HTTPError as e:
        if e.code >= 400:
            raise ServerError(f'Got {e.code}: {e}')
        
        else:
            RequestError.from_code(e.code, e)
    
    except Exception as e:
        raise MappError(f'Error creating model: {e}')

def http_model_read(ctx: MappContext, model_class: type, model_id: str) -> object:

    # init #

    module_kebab = model_class._model_spec['module']['kebab_case']
    model_kebab = model_class._model_spec['name']['kebab_case']
    url = f'{ctx.host}/api/{module_kebab}/{model_kebab}/{model_id}'

    # send request #

    try:
        request = Request(url, headers=ctx.headers, method='GET')
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return from_json(model_class, response_body)
        
    except HTTPError as e:
        if e.code >= 400:
            raise ServerError(f'Got {e.code}: {e}')
        
        else:
            raise RequestError.from_code(e.code, e)
    
    except Exception as e:
        raise MappError(f'Error reading model: {e}')

def http_model_update(ctx: MappContext, model_class: type, model_id: str, model: object) -> object:

    # init #

    module_kebab = model_class._model_spec['module']['kebab_case']
    model_kebab = model_class._model_spec['name']['kebab_case']
    url = f'{ctx.host}/api/{module_kebab}/{model_kebab}/{model_id}'
    request_body = json.dumps(model._asdict()).encode()

    # send request #

    try:
        request = Request(url, headers=ctx.headers, method='PUT', data=request_body)
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return from_json(model_class, response_body)
        
    except HTTPError as e:
        if e.code >= 400:
            raise ServerError(f'Got {e.code}: {e}')
        
        else:
            raise RequestError.from_code(e.code, e)

    except Exception as e:
        raise MappError(f'Error updating model: {e}')

def http_model_delete(ctx: MappContext, model_class: type, model_id: str):

    # init #

    module_kebab = model_class._model_spec['module']['kebab_case']
    model_kebab = model_class._model_spec['name']['kebab_case']
    url = f'{ctx.host}/api/{module_kebab}/{model_kebab}/{model_id}'

    # send request #

    try:
        request = Request(url, headers=ctx.headers, method='DELETE')
        with urlopen(request) as response:
            _ = response.read().decode('utf-8')

    except HTTPError as e:
        if e.code >= 400:
            raise ServerError(f'Got {e.code}: {e}')
        
        else:
            raise RequestError.from_code(e.code, e)
        
    except Exception as e:
        raise MappError(f'Error deleting model: {e}')

def http_model_list(ctx: MappContext, model_class: type, offset: int = 0, limit: int = 50) -> dict:

    # init #

    module_kebab = model_class._model_spec['module']['kebab_case']
    model_kebab = model_class._model_spec['name']['kebab_case']
    url = f'{ctx.host}/api/{module_kebab}/{model_kebab}?offset={offset}&limit={limit}'

    # send request #

    try:
        request = Request(url, headers=ctx.headers, method='GET')
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return list_from_json(response_body, model_class)
        
    except HTTPError as e:
        if e.code >= 400:
            raise ServerError(f'Got {e.code}: {e}')
        
        else:
            raise RequestError.from_code(e.code, e)
        
    except Exception as e:
        raise MappError(f'Error listing models: {e}')
