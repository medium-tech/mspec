from core.exceptions import MSpecError, ConfigError, NotFoundError, AuthenticationError, ForbiddenError
from test_module.test_model.model import TestModel

import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

# vars :: {"test_module": "module.name.snake_case", "test-module": "module.name.kebab_case"}
# vars :: {"test_model": "model.name.snake_case", "test model": "model.name.lower_case", "test-model": "model.name.kebab_case", "TestModel": "model.name.pascal_case"}

__all__ = [
    'client_create_test_model',
    'client_read_test_model',
    'client_update_test_model',
    'client_delete_test_model',
    'client_list_test_model'
]

def client_create_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    create a test model on the server, verifying the data first.
    
    args ::
        ctx :: dict containing the client context.
        obj :: the TestModel object to create.
    
    return :: TestModel object with the new id.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/test-module/test-model'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return TestModel.from_json(response_body)
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating test model: {e.__class__.__name__}: {e}')

def client_read_test_model(ctx:dict, id:str) -> TestModel:
    """
    read a test model from the server, verifying it first.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to read.
    
    return :: profile object if it exists.

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/test-module/test-model/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:

        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error reading test model: invalid username or password')
        elif e.code == 403:
            raise ForbiddenError('Error reading test model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'test model {id} not found')
        raise MSpecError(f'error reading test model: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading test model: {e.__class__.__name__}: {e}')
    
    return TestModel.from_json(response_body).validate()

def client_update_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    update a test model on the server, verifying the data first.

    args ::
        ctx :: dict containing the client context.
        obj :: the TestModel object to update.
    
    return :: TestModel object.

    raises :: ConfigError, MSpecError, NotFoundError
    """
    try:
        _id = obj.id
    except KeyError:
        raise ValueError('invalid data, missing id')

    if _id is None:
        raise ValueError('invalid data, missing id')

    try:
        url = f'{ctx["host"]}/api/test-module/test-model/{_id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
    
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error updating test model: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error updating test model: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'test model {id} not found')
        raise MSpecError(f'error updating test model: {e.__class__.__name__}: {e}')
        
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating test model: {e.__class__.__name__}: {e}')
    
    return TestModel.from_json(response_body).validate()

def client_delete_test_model(ctx:dict, id:str) -> None:
    """
    delete a test model from the server.

    args ::
        ctx :: dict containing the client context.
        id :: str of the id of the item to delete.
    
    return :: None

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/test-module/test-model/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as response:
            _ = response.read().decode('utf-8')

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting test model: {e.__class__.__name__}: {e}')

def client_list_test_model(ctx:dict, offset:int=0, limit:int=50) -> list[TestModel]:
    """
    list test models from the server, verifying each.

    args ::
        ctx :: dict containing the client context.
        offset :: int of the offset to start listing from.
        limit :: int of the maximum number of items to list.
    
    return :: list of TestModel objects.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/test-module/test-model?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')
        
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')

        return [TestModel(**item).validate() for item in json.loads(response_body)]

    except (json.JSONDecodeError, TypeError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing test models: {e.__class__.__name__}: {e}')