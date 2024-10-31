from sample_module.example_item import *

import json

from urllib.request import Request, urlopen

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
        data :: the data to create the item with.
    
    return :: the id of the created item.
    """

    request_body = example_item_to_json(example_item_verify(data)).encode()

    try:
        request = Request(f'{ctx["host"]}/api/sample-module/example-item', headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        id = json.loads(response_body)['id']
        if not isinstance(id, str):
            raise Exception('invalid response from server, id must be a string')
        return id
    
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error creating example item: {e.__class__.__name__}: {e}')

def client_read_example_item(ctx:dict, id:str) -> dict|None:
    """
    read a example item from the server, verifying it.

    args ::
        id :: the id of the item to read.
    
    return :: dict of the item if it exists, None otherwise.
    """

    try:
        request = Request(ctx['host'] + '/api/sample-module/example-item/' + id, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return example_item_verify(json.loads(response_body))
    
    except (json.JSONDecodeError, TypeError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error reading example item: {e.__class__.__name__}: {e}')

def client_update_example_item(ctx:dict, id:str, data:dict) -> bool:
    """
    update a example item on the server, verifying the data first.

    args ::
        id :: the id of the item to update.
        data :: the data to update the item with.
    
    return :: true if the item was updated, false otherwise.
    """

    request_body = example_item_to_json(example_item_verify(data)).encode()

    try:
        request = Request(f'{ctx["host"]}/api/sample-module/example-item/{id}', headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as _:
            """we dont need the response"""
        
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise Exception(f'error updating example item: {e.__class__.__name__}: {e}')

def client_delete_example_item(ctx:dict, id:str):
    """
    delete a example item from the server.

    args ::
        id :: the id of the item to delete.
    
    return :: None
    """

    try:
        request = Request(f'{ctx["host"]}/api/sample-module/example-item/{id}', headers=ctx['headers'], method='DELETE')

        with urlopen(request) as _:
            """we dont need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise Exception(f'error deleting example item: {e.__class__.__name__}: {e}')

def client_list_example_item(ctx:dict, offset:int=0, limit:int=25):
    """
    list example items from the server, verifying each.

    args ::
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of items.
    """

    try:
        request = Request(f'{ctx["host"]}/api/sample-module/example-item?offset={offset}&limit={limit}', headers=ctx['headers'], method='GET')
        
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return [example_item_verify(item) for item in json.loads(response_body)['items']]

    except (json.JSONDecodeError, TypeError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise Exception(f'error listing example items: {e.__class__.__name__}: {e}')
