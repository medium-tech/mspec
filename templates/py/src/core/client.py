import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from copy import deepcopy

from core.exceptions import MSpecError, ConfigError, NotFoundError, AuthenticationError, ForbiddenError
from core.models import *

__all__ = [
    'create_client_context',
    
    'client_login',
    'client_create_user',
    'client_read_user',
    'client_update_user',
    'client_delete_user',
    'client_list_users'
]


# vars :: {"http://localhost:5005": "client.default_host"}

"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

default_host = os.environ.get('MSPEC_CLIENT_HOST', 'http://localhost:5005')

def create_client_context(host:str=default_host) -> dict:
    """
    initialize the client with a host. if host is not provided,
    it will use the value of the `MSPEC_CLIENT_HOST` environment variable,
    if that is not set, it will use the value for environment variable `MSPEC_CLIENT_HOST`.
    
    args ::
        host :: the host to connect to.
    
    return :: None
    """.format(default_host)

    return deepcopy({
        'host': host,
        'headers': {
            'Content-Type': 'application/json'
        }
    })

# user #

def client_login(ctx:dict, email:str, password:str) -> dict:
    """
    login to the server, returning the context to be used for other client requests.
    
    args ::
        email :: str of the email of the user to login.
        password :: str of the password of the user to login.
    
    return :: dict with client context
        {
            'host': ctx['host'],
            'headers': {
                'Authorization': f'Bearer <token>'
            }
        }

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/auth/login'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = urlencode({'email': email, 'password': password}).encode('utf-8')

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = json.loads(response.read().decode('utf-8'))

    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error logging in: invalid username or password')
        else:
            raise MSpecError(f'error logging in: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error logging in: {e.__class__.__name__}: {e}')
    
    login_ctx = {
        'host': ctx['host'],
        'headers': deepcopy(ctx['headers'])
    }
    login_ctx['headers']['Authorization'] = f'Bearer {response_body["access_token"]}'
    return login_ctx

def client_create_user(ctx:dict, new_user:CreateUser) -> User:
    """
    create a user on the server, verifying the data first.
    
    args ::
        new_user: create_user_form object to create.
    
    return :: user object with new id

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/user'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = new_user.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return User.from_json(response_body)
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating user: {e.__class__.__name__}: {e}')
    
def client_read_user(ctx:dict, id:str) -> User:
    """
    read a user from the server, verifying it before returning.

    args ::
        ctx :: dict of the client context.
        id :: str of the id of the user to read.
    
    return :: user object if it exists

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/core/user/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')
    request = Request(url, headers=ctx['headers'], method='GET')

    try:

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
    
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error reading user: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error reading user: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'user {id} not found')
        raise MSpecError(f'error reading user: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading user: {e.__class__.__name__}: {e}')

    return User.from_json(response_body).validate()
    
def client_update_user(ctx:dict, obj:User) -> User:
    """
    update a user on the server, verifying the data first.

    args ::
        ctx :: dict of the client context.
        obj :: user object
    
    return :: User object

    raises :: ConfigError, MSpecError, NotFoundError
    """
    try:
        _id = obj.id
    except KeyError:
        raise ValueError('invalid data, missing id')
    
    try:
        url = ctx['host'] + '/api/core/user/' + _id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as _response:
            return obj
        
    except HTTPError as e:
        if e.code == 401:
            raise AuthenticationError('Error updating user: authentication error')
        elif e.code == 403:
            raise ForbiddenError('Error updating user: forbidden')
        elif e.code == 404:
            raise NotFoundError(f'user {id} not found')
        raise MSpecError(f'error updating user: {e.__class__.__name__}: {e}')
            
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating user: {e.__class__.__name__}: {e}')
    
def client_delete_user(ctx:dict, id:str) -> None:
    """
    delete a user from the server.

    args ::
        ctx :: dict of the client context.
        id :: str of the id of the user to delete.
    
    return :: None

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = f'{ctx["host"]}/api/core/user/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as _response:
            """we don't need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting user: {e.__class__.__name__}: {e}')
    
def client_list_users(ctx:dict, offset:int=0, limit:int=50) -> list[User]:
    """
    list users from the server, verifying each.

    args ::
        offset :: int of the number of users to skip.
        limit :: int of the number of users to return.
    
    return :: list of User objects

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/user?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request = Request(url, headers=ctx['headers'], method='GET')

    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
        
        return [User(**item).validate() for item in json.loads(response_body)]
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing users: {e.__class__.__name__}: {e}')
