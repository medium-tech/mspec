import os
import json
from urllib.request import Request, urlopen

"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

from msample import verify, to_json

__all__ = ['client_init', 'client_create_sample_item', 'client_read_sample_item', 'client_update_sample_item', 'client_delete_sample_item', 'client_list_sample_item']

client_host = None
default_client_host = 'http://localhost:9009'
endpoint = f'/api/sample/sample-item'

def client_init(host:str=None) -> str:
    """
    initialize the client with a host. if host is not provided,
    it will use the value of the MSPEC_CLIENT_HOST environment variable,
    if that is not set, it will use '{}'.
    
    args ::
        host :: the host to connect to.
    
    return :: None
    """.format(default_client_host)
    global client_host
    if host is None:
        client_host = os.environ.get('MSPEC_CLIENT_HOST', default_client_host)
    else:
        client_host = host
    return client_host


headers = {'Content-Type': 'application/json'}

def client_create_sample_item(data:dict) -> str:
    """
    create a sample item on the server, verifying the data first.
    
    args ::
        data :: the data to create the item with.
    
    return :: the id of the created item.
    """

    request_body = to_json(verify(data)).encode()
    request = Request(f'{client_host}{endpoint}', headers=headers, method='POST', data=request_body)

    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        id = json.loads(response_body)['id']
        if not isinstance(id, str):
            raise Exception('invalid response from server, id must be a string')
        return id
    
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error creating sample item: {e.__class__.__name__}: {e}')

def client_read_sample_item(id:str) -> dict|None:
    """
    read a sample item from the server, verifying it.

    args ::
        id :: the id of the item to read.
    
    return :: dict of the item if it exists, None otherwise.
    """

    request = Request(f'{client_host}{endpoint}/{id}', headers=headers, method='GET')

    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return verify(json.loads(response_body))
    
    except (json.JSONDecodeError, TypeError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error reading sample item: {e.__class__.__name__}: {e}')

def client_update_sample_item(id:str, data:dict) -> bool:
    """
    update a sample item on the server, verifying the data first.

    args ::
        id :: the id of the item to update.
        data :: the data to update the item with.
    
    return :: true if the item was updated, false otherwise.
    """

    request_body = to_json(verify(data)).encode()
    request = Request(f'{client_host}{endpoint}/{id}', headers=headers, method='PUT', data=request_body)

    try:
        with urlopen(request) as response:
            pass
    
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error updating sample item: {e.__class__.__name__}: {e}')

def client_delete_sample_item(id:str):
    """
    delete a sample item from the server.

    args ::
        id :: the id of the item to delete.
    
    return :: None
    """

    request = Request(f'{client_host}{endpoint}/{id}', headers=headers, method='DELETE')

    try:
        with urlopen(request) as response:
            pass
    
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error deleting sample item: {e.__class__.__name__}: {e}')

def client_list_sample_item(offset:int=0, limit:int=25):
    """
    list sample items from the server, verifying each.

    args ::
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of items.
    """

    request = Request(f'{client_host}{endpoint}?offset={offset}&limit={limit}', headers=headers, method='GET')

    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return [verify(item) for item in json.loads(response_body)['items']]
    
    except (json.JSONDecodeError, TypeError) as e:
        raise Exception('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise Exception(f'error listing sample items: {e.__class__.__name__}: {e}')
