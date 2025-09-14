from core.exceptions import MSpecError, ConfigError, NotFoundError, AuthenticationError, ForbiddenError
from template_module.single_model.model import SingleModel

import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

# vars :: {"template_module": "module.name.snake_case", "template-module": "module.name.kebab_case"}
# vars :: {"single_model": "model.name.snake_case", "single model": "model.name.lower_case", "single-model": "model.name.kebab_case", "SingleModel": "model.name.pascal_case"}

__all__ = [
    'client_create_single_model',
    'client_read_single_model',
    'client_update_single_model',
    'client_delete_single_model',
    'client_list_single_model'
]

def client_create_single_model(ctx:dict, obj:SingleModel) -> SingleModel:
    """
    create a single model on the server, verifying the data first.
    
    args ::
        ctx :: dict containing the client context.
        obj :: the SingleModel object to create.
    
    return :: SingleModel object with the new id.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/single-model'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return SingleModel(**json.loads(response_body)).convert_types()
        
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error creating single model: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error creating single model: forbidden')

        raise MSpecError(f'error creating single model: {e.__class__.__name__}: {e}')

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError(f'invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating single model: {e.__class__.__name__}: {e}')

def client_read_single_model(ctx:dict, id:str) -> SingleModel:
    """
    read a single model from the server, verifying it first.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to read.
    
    return :: profile object if it exists.

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/template-module/single-model/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:

        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error reading single model: invalid username or password')
        elif e.code == 403:
            raise ForbiddenError('Error reading single model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'single model {id} not found')
        raise MSpecError(f'error reading single model: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading single model: {e.__class__.__name__}: {e}')

    return SingleModel(**json.loads(response_body)).convert_types()

def client_update_single_model(ctx:dict, obj:SingleModel) -> SingleModel:
    """
    update a single model on the server, verifying the data first.

    args ::
        ctx :: dict containing the client context.
        obj :: the SingleModel object to update.
    
    return :: SingleModel object.

    raises :: ConfigError, MSpecError, NotFoundError
    """
    try:
        _id = obj.id
    except KeyError:
        raise ValueError('invalid data, missing id')

    if _id is None:
        raise ValueError('invalid data, missing id')

    try:
        url = f'{ctx["host"]}/api/template-module/single-model/{_id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
    
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error updating single model: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error updating single model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'single model {id} not found')
        raise MSpecError(f'error updating single model: {e.__class__.__name__}: {e}')
        
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating single model: {e.__class__.__name__}: {e}')

    return SingleModel(**json.loads(response_body)).convert_types()

def client_delete_single_model(ctx:dict, id:str) -> None:
    """
    delete a single model from the server.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to delete.
    
    return :: None

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/single-model/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as response:
            _ = response.read().decode('utf-8')

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting single model: {e.__class__.__name__}: {e}')

def client_list_single_model(ctx:dict, offset:int=0, limit:int=50) -> list[SingleModel]:
    """
    list single models from the server, verifying each.

    args ::
        ctx :: dict containing the client context.
        offset :: int of the offset to start listing from.
        limit :: int of the maximum number of items to list.
    
    return :: list of SingleModel objects.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/single-model?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')
        
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        response_data = json.loads(response_body)

        return {
            'total': response_data['total'],
            'items': [SingleModel(**item).convert_types() for item in response_data['items']]
        }

    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError(f'invalid response from server, {e.__class__.__name__}: {e}')

    except Exception as e:
        raise MSpecError(f'error listing single models: {e.__class__.__name__}: {e}')