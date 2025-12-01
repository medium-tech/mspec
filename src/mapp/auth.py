import os
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from mapp.context import MappContext
from mapp.errors import AuthenticationError, MappError
from mapp.types import new_model_class

MAPP_AUTH_SECRET_KEY = os.environ.get('MAPP_AUTH_SECRET_KEY')   # openssl rand -hex 32
MAPP_AUTH_LOGIN_EXPIRATION_MINUTES = os.environ.get('MAPP_AUTH_LOGIN_EXPIRATION_MINUTES', 60 * 24 * 7)

__all__ = [
    'User',
    'PasswordHash',
    'init_auth_module',
    'create_user',
    'login_user',
    'current_user',
    'logout_user',
    'delete_user'
]

class User(NamedTuple):
    id: str
    name: str
    email: str


class PasswordHash(NamedTuple):
    id: str
    user_id: str
    hash: str


def init_auth_module(spec: dict) -> bool:
    """
    If spec.project.use_builtin_modules is True:
        Initialize the auth module User and PasswordHash model classes.

    This is needed because builtin models are defined by the same yaml spec
    that the app is based on. For db functions to work, the model classes need to
    have their _model_spec and _module_spec attributes set from the spec loaded
    from the environment.

    return :: bool
        True if auth module initialized, else False
    """

    if spec['project']['use_builtin_modules'] is False:
        return False
    
    try:
        auth_module = spec['modules']['auth']
        user = auth_module['models']['user']
        password_hash = auth_module['models']['password_hash']
    except KeyError as e:
        raise MappError('INVALID_SPEC', f'Builtin auth module is missing key: {e}')
    
    global User
    global PasswordHash

    User._model_spec = user
    User._module_spec = auth_module

    PasswordHash._model_spec = password_hash
    PasswordHash._module_spec = auth_module

    return True

#
# internal
#

def _verify_password(plain_password:str, hashed_password:str) -> bool:
    pass

def _get_password_hash(password:str) -> str:
    pass

def _check_user_credentials(ctx: MappContext, email: str, password: str) -> str:
    """
    returns user id if credentials are valid, else raises AuthenticationError

    args ::
        ctx :: dict containing the database client
        email :: user email
        password :: user password
    
    return :: str of user id
    raises :: AuthenticationError
    """
    
    user_id_result = ctx.db.cursor.execute(
        "SELECT id FROM user WHERE email = ?",
        (email.lower(),)
    ).fetchone()

    if user_id_result is None:
        raise AuthenticationError()
    
    pw_hash_result = ctx.db.cursor.execute(
        "SELECT hash FROM password_hash WHERE user_id = ?", 
        (user_id_result[0],)
    ).fetchone()

    if pw_hash_result is None:
        raise AuthenticationError()

    if not _verify_password(password, pw_hash_result[0]):
        raise AuthenticationError()
    
    return str(user_id_result[0])

def _create_access_token(data: dict):
    expires = datetime.now(timezone.utc) + timedelta(minutes=MAPP_AUTH_LOGIN_EXPIRATION_MINUTES)

    data_to_encode = data.copy()
    data_to_encode.update({'exp': expires})

    if MAPP_AUTH_SECRET_KEY is None:
        raise AuthenticationError()
    
    token = jwt.encode(data_to_encode, MAPP_AUTH_SECRET_KEY, algorithm='HS256')
    return token, 'bearer'

def _get_user_id_from_token(ctx:dict, token:str) -> str:
    """parse a JWT token and return the user id as a string,
    raise AuthenticationError if the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, MAPP_AUTH_SECRET_KEY, algorithms=['HS256'])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise AuthenticationError('Could not validate credentials')
        return user_id
    except JWTError:
        raise AuthenticationError('Could not validate credentials')


#
# extneral
#

def create_user(ctx: MappContext, **params) -> dict:
    """
    Create a new user in the auth module.
    ctx: MappContext - The application context.
    params: dict - Parameters for the new user.
        name: str - The name of the user.
        email: str - The email of the user.
        password: str - The password for the user.
        password_confirm: str - Confirmation of the password.

    return: dict
        id: str - The ID of the newly created user.
        name: str - The name of the newly created user.
        email: str - The email of the newly created user.
    """

def login_user(ctx: MappContext, **params):
    """
    Log in a user in the auth module.
    ctx: MappContext - The application context.
    params: dict - Parameters for login.
        email: str - The email of the user.
        password: str - The password for the user.

    return: dict
        access_token: str - The access token for the logged-in user.
        token_type: str - The type of the token.
    """

def current_user(ctx: MappContext, **params):
    """
    Get the current logged-in user in the auth module.
    ctx: MappContext - The application context.
    params: dict - No params needed for current user.

    return: dict
        id: str - The ID of the current user.
        name: str - The name of the current user.
        email: str - The email of the current user.
    """

def logout_user(ctx: MappContext, **params):
    """
    Log out a user in the auth module.
    ctx: MappContext - The application context.
    params: dict - No params needed for logout.

    return: dict
        acknowledged: bool - Whether the logout was successful.
        message: str - Confirmation message of logout.
    """

def delete_user(ctx: MappContext, **params):
    """
    Delete a user in the auth module.
    ctx: MappContext - The application context.
    params: dict - Parameters for deleting a user.
        user_id: str - The ID of the user to delete.

    return: dict
        acknowledged: bool - Whether the deletion was successful.
        message: str - Confirmation message of deletion.
    """
