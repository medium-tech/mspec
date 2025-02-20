from core.exceptions import MSpecError, ConfigError, NotFoundError, AuthenticationError, ForbiddenError
from sample_module.example_item.model import ExampleItem

import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

# vars :: {"sample_module": "module.name.snake_case", "sample-module": "module.name.kebab_case"}
# vars :: {"http://localhost:9009": "client.default_host", "example_item": "model.name.snake_case", "example item": "model.name.lower_case", "example-item": "model.name.kebab_case"}

__all__ = [
    'client_create_example_item',
    'client_read_example_item',
    'client_update_example_item',
    'client_delete_example_item',
    'client_list_example_item'
]

def client_create_example_item(ctx:dict, obj:ExampleItem) -> ExampleItem:
    """
    create a example item on the server, verifying the data first.
    
    args ::
        ctx :: dict containing the client context.
        obj :: the ExampleItem object to create.
    
    return :: ExampleItem object with the new id.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return ExampleItem.from_json(response_body)
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating example item: {e.__class__.__name__}: {e}')

def client_read_example_item(ctx:dict, id:str) -> ExampleItem:
    """
    read a example item from the server, verifying it first.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to read.
    
    return :: profile object if it exists.

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/sample-module/example-item/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:

        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error reading example item: invalid username or password')
        elif e.code == 403:
            raise ForbiddenError('Error reading example item: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'example item {id} not found')
        raise MSpecError(f'error reading example item: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading example item: {e.__class__.__name__}: {e}')
    
    return ExampleItem.from_json(response_body).validate()

def client_update_example_item(ctx:dict, obj:ExampleItem) -> ExampleItem:
    """
    update a example item on the server, verifying the data first.

    args ::
        ctx :: dict containing the client context.
        obj :: the ExampleItem object to update.
    
    return :: ExampleItem object.

    raises :: ConfigError, MSpecError, NotFoundError
    """
    try:
        _id = obj.id
    except KeyError:
        raise ValueError('invalid data, missing id')

    if _id is None:
        raise ValueError('invalid data, missing id')

    try:
        url = f'{ctx["host"]}/api/sample-module/example-item/{_id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as _response:
            return obj
    
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error updating example item: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error updating example item: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'example item {id} not found')
        raise MSpecError(f'error updating example item: {e.__class__.__name__}: {e}')
        
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating example item: {e.__class__.__name__}: {e}')

def client_delete_example_item(ctx:dict, id:str) -> None:
    """
    delete a example item from the server.

    args ::
        ctx :: dict containing the client context.
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

        with urlopen(request) as _response:
            """we don't need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting example item: {e.__class__.__name__}: {e}')

def client_list_example_item(ctx:dict, offset:int=0, limit:int=50) -> list[ExampleItem]:
    """
    list example items from the server, verifying each.

    args ::
        ctx :: dict containing the client context.
        offset :: int of the offset to start listing from.
        limit :: int of the maximum number of items to list.
    
    return :: list of ExampleItem objects.

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

        return [ExampleItem(**item).validate() for item in json.loads(response_body)]

    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing example items: {e.__class__.__name__}: {e}')
