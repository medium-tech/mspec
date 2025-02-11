import json

from urllib.request import Request, urlopen

from core.exceptions import MSpecError, ConfigError, NotFoundError
from sample_module.example_item import *



# vars :: {"sample_module": "module.name.snake_case", "sample-module": "module.name.kebab_case"}
# vars :: {"http://localhost:9009": "client.default_host", "example_item": "model.name.snake_case", "example item": "model.name.lower_case", "example-item": "model.name.kebab_case"}


"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

__all__ = [
    'client_create_example_item',
    'client_read_example_item',
    'client_update_example_item',
    'client_delete_example_item',
    'client_list_example_item'
]

def client_create_example_item(ctx:dict, data:dict) -> str:
    """
    create a example item on the server, verifying the data first.
    
    args ::
        data :: dict of the data to create the item with.
    
    return :: str of the id of the created item.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = example_item_to_json(example_item_validate(data)).encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        id = json.loads(response_body)['id']
        if not isinstance(id, str):
            raise MSpecError('invalid response from server, id must be a string')
        return id
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating example item: {e.__class__.__name__}: {e}')

def client_read_example_item(ctx:dict, id:str) -> dict:
    """
    read a example item from the server, verifying it first.

    args ::
        id :: str of the id of the item to read.
    
    return :: dict of the item if it exists

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/sample-module/example-item/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            if response.status == 404:
                raise NotFoundError(f'example item {id} not found')
            response_body = response.read().decode('utf-8')

        return example_item_validate(example_item_from_json(response_body))
    
    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading example item: {e.__class__.__name__}: {e}')

def client_update_example_item(ctx:dict, id:str, data:dict) -> None:
    """
    update a example item on the server, verifying the data first.

    args ::
        id :: str of the id of the item to update.
        data :: the data to update the item with.
    
    return :: None

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = example_item_to_json(example_item_validate(data)).encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as response:
            if response.status == 404:
                raise NotFoundError(f'example item {id} not found')
        
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating example item: {e.__class__.__name__}: {e}')

def client_delete_example_item(ctx:dict, id:str) -> None:
    """
    delete a example item from the server.

    args ::
        id :: str of the id of the item to delete.
    
    return :: None

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as _:
            """we don't need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting example item: {e.__class__.__name__}: {e}')

def client_list_example_item(ctx:dict, offset:int=0, limit:int=50) -> list[dict]:
    """
    list example items from the server, verifying each.

    args ::
        offset :: int of the offset to start listing from.
        limit :: int of the maximum number of items to list.
    
    return :: list of dicts of items.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')
        
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return [example_item_validate(example_item_from_json(item)) for item in json.loads(response_body)['items']]

    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing example items: {e.__class__.__name__}: {e}')
