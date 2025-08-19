from core.exceptions import MSpecError, ConfigError, NotFoundError, AuthenticationError, ForbiddenError
from template_module.multi_model.model import MultiModel

import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

__all__ = [
    'client_create_multi_model',
    'client_read_multi_model',
    'client_update_multi_model',
    'client_delete_multi_model',
    'client_list_multi_model'
]

def client_create_multi_model(ctx:dict, obj:MultiModel) -> MultiModel:
    """
    create a multi model on the server, verifying the data first.

    args ::
        ctx :: dict containing the client context.
        obj :: the MultiModel object to create.

    return :: MultiModel object with the new id.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/multi-model'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return MultiModel(**json.loads(response_body)).convert_types()

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError(f'invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating multi model: {e.__class__.__name__}: {e}')

def client_read_multi_model(ctx:dict, id:str) -> MultiModel:
    """
    read a multi model from the server, verifying it first.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to read.
    
    return :: profile object if it exists.

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/template-module/multi-model/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:

        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error reading multi model: invalid username or password')
        elif e.code == 403:
            raise ForbiddenError('Error reading multi model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'multi model {id} not found')
        raise MSpecError(f'error reading multi model: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading multi model: {e.__class__.__name__}: {e}')

    return MultiModel(**json.loads(response_body)).convert_types()

def client_update_multi_model(ctx:dict, obj:MultiModel) -> MultiModel:
    """
    update a multi model on the server, verifying the data first.

    args ::
        ctx :: dict containing the client context.
        obj :: the MultiModel object to update.
    
    return :: MultiModel object.

    raises :: ConfigError, MSpecError, NotFoundError
    """
    try:
        _id = obj.id
    except KeyError:
        raise ValueError('invalid data, missing id')

    if _id is None:
        raise ValueError('invalid data, missing id')

    try:
        url = f'{ctx["host"]}/api/template-module/multi-model/{_id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
    
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error updating multi model: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error updating multi model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'multi model {id} not found')
        raise MSpecError(f'error updating multi model: {e.__class__.__name__}: {e}')
        
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError(f'invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating multi model: {e.__class__.__name__}: {e}')

    return MultiModel(**json.loads(response_body)).convert_types()

def client_delete_multi_model(ctx:dict, id:str) -> None:
    """
    delete a multi model from the server.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to delete.
    
    return :: None

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/multi-model/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as response:
            _ = response.read().decode('utf-8')

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting multi model: {e.__class__.__name__}: {e}')

def client_list_multi_model(ctx:dict, offset:int=0, limit:int=50) -> list[MultiModel]:
    """
    list multi models from the server, verifying each.

    args ::
        ctx :: dict containing the client context.
        offset :: int of the offset to start listing from.
        limit :: int of the maximum number of items to list.
    
    return :: list of MultiModel objects.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/template-module/multi-model?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')
        
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return [MultiModel(**item).convert_types() for item in json.loads(response_body)]

    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError(f'invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing multi models: {e.__class__.__name__}: {e}')