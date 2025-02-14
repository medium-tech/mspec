import os
import json

from urllib.request import Request, urlopen
from urllib.error import HTTPError

from core.exceptions import MSpecError, ConfigError, NotFoundError
from core.models import *

__all__ = [
    'create_client_context',
    
    'client_create_user',
    'client_read_user',
    'client_update_user',
    'client_delete_user',
    'client_list_users',
    
    'client_create_profile',
    'client_read_profile',
    'client_update_profile',
    'client_delete_profile',
    'client_list_profile'
]


# vars :: {"http://localhost:9009": "client.default_host"}

"""
WARNING: urlib.request module is unsafe to use with os.fork on OSX
    ref: https://docs.python.org/3/library/urllib.request.html#urllib.request.urlopen
"""

default_host = os.environ.get('MSPEC_CLIENT_HOST', 'http://localhost:9009')

def create_client_context(host:str=default_host) -> dict:
    """
    initialize the client with a host. if host is not provided,
    it will use the value of the `MSPEC_CLIENT_HOST` environment variable,
    if that is not set, it will use the value for environment variable `MSPEC_CLIENT_HOST`.
    
    args ::
        host :: the host to connect to.
    
    return :: None
    """.format(default_host)

    return {
        'host': host,
        'headers': {
            'Content-Type': 'application/json'
        }
    }

# user #

def client_create_user(ctx:dict, obj:user) -> user:
    """
    create a user on the server, verifying the data first.
    
    args ::
        obj :: user obejct
    
    return :: user object with new id

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/user'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = obj.validate().to_json().encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return user.from_json(response_body)
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating user: {e.__class__.__name__}: {e}')
    
def client_read_user(ctx:dict, id:str) -> user:
    """
    read a user from the server, verifying it before returning.

    args ::
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
            if response.status == 404:
                raise NotFoundError(f'user {id} not found')
            response_body = response.read().decode('utf-8')
        
        return user.from_json(response_body).validate()
    
    except HTTPError as e:
        if e.code == 404:
            raise NotFoundError(f'user {id} not found')
        raise MSpecError(f'error reading user: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading user: {e.__class__.__name__}: {e}')
    
def client_update_user(ctx:dict, obj:user) -> None:
    """
    update a user on the server, verifying the data first.

    args ::
        obj :: user object
    
    return :: None

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

        with urlopen(request) as response:
            if response.status == 404:
                raise NotFoundError(f'user {_id} not found')
            
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating user: {e.__class__.__name__}: {e}')
    
def client_delete_user(ctx:dict, id:str) -> None:
    """
    delete a user from the server.

    args ::
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

        with urlopen(request) as _:
            """we don't need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting user: {e.__class__.__name__}: {e}')
    
def client_list_users(ctx:dict, offset:int=0, limit:int=50) -> list[user]:
    """
    list users from the server, verifying each.

    args ::
        offset :: int of the number of users to skip.
        limit :: int of the number of users to return.
    
    return :: list of dicts of the users.

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
        
        return [user(**item).validate() for item in json.loads(response_body)]
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error listing users: {e.__class__.__name__}: {e}')
    
# profile #

def client_create_profile(ctx:dict, data:dict) -> dict:
    """
    create a profile on the server, verifying the data first.
    
    args ::
        data :: dict of the data to create the profile with.
    
    return :: dict of the the created profile.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/profile'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = profile_to_json(profile_validate(data)).encode()

    try:
        request = Request(url, headers=ctx['headers'], method='POST', data=request_body)

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            return profile_from_json(response_body)
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error creating profile: {e.__class__.__name__}: {e}')
    
def client_read_profile(ctx:dict, id:str) -> dict:
    """
    read a profile from the server, verifying it first.

    args ::
        id :: str of the id of the profile to read.
    
    return :: dict of the profile if it exists

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        url = ctx['host'] + '/api/core/profile/' + id
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request = Request(url, headers=ctx['headers'], method='GET')

    try:

        with urlopen(request) as response:
            if response.status == 404:
                raise NotFoundError(f'profile {id} not found')
            response_body = response.read().decode('utf-8')
        
        return profile_validate(profile_from_json(response_body))
    
    except HTTPError as e:
        if e.code == 404:
            raise NotFoundError(f'profile {id} not found')
        raise MSpecError(f'error reading profile: {e.__class__.__name__}: {e}')
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error reading profile: {e.__class__.__name__}: {e}')
    
def client_update_profile(ctx:dict, data:dict) -> None:
    """
    update a profile on the server, verifying the data first.

    args ::
        data :: dict of the data to update the profile with.
    
    return :: None

    raises :: ConfigError, MSpecError, NotFoundError
    """

    try:
        _id = data['id']
    except KeyError:
        raise ValueError('invalid data, missing id')

    try:
        url = f'{ctx["host"]}/api/core/profile/{_id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    request_body = profile_to_json(profile_validate(data)).encode()

    try:
        request = Request(url, headers=ctx['headers'], method='PUT', data=request_body)

        with urlopen(request) as response:
            if response.status == 404:
                raise NotFoundError(f'profile {_id} not found')
            
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error updating profile: {e.__class__.__name__}: {e}')
    
def client_delete_profile(ctx:dict, id:str) -> None:
    """
    delete a profile from the server.

    args ::
        id :: str of the id of the profile to delete.
    
    return :: None

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/profile/{id}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='DELETE')

        with urlopen(request) as _:
            """we don't need the response"""

    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    
    except Exception as e:
        raise MSpecError(f'error deleting profile: {e.__class__.__name__}: {e}')
    
def client_list_profile(ctx:dict, offset:int=0, limit:int=50) -> list[dict]:
    """
    list profiles from the server, verifying each.

    args ::
        offset :: int of the number of profiles to skip.
        limit :: int of the number of profiles to return.
    
    return :: list of dicts of the profiles.

    raises :: ConfigError, MSpecError
    """

    try:
        url = f'{ctx["host"]}/api/core/profile?offset={offset}&limit={limit}'
    except KeyError:
        raise ConfigError('invalid context, missing host')

    try:
        request = Request(url, headers=ctx['headers'], method='GET')

        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
        
        return [profile_validate(item) for item in json.loads(response_body)]
    
    except (json.JSONDecodeError, KeyError) as e:
        raise MSpecError('invalid response from server, {e.__class__.__name__}: {e}')
    except Exception as e:
        raise MSpecError(f'error listing profiles: {e.__class__.__name__}: {e}')
