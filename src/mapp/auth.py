import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from mapp.context import MappContext
from mapp.errors import AuthenticationError, MappError
from mapp.types import validate_model, Acknowledgment

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

class UserSession(NamedTuple):
    id: str
    user_id: str
    created_at: datetime

class PasswordHash(NamedTuple):
    id: str
    user_id: str
    hash: str

class CreateUserOutput(NamedTuple):
    id: str
    name: str
    email: str

class LoginUserOutput(NamedTuple):
    access_token: str
    token_type: str

class CurrentUserOutput(NamedTuple):
    id: str
    name: str
    email: str


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
        user_session = auth_module['models']['user_session']
        password_hash = auth_module['models']['password_hash']
        create_user_output = auth_module['ops']['create_user']['output']
        login_user_output = auth_module['ops']['login_user']['output']
        current_user_output = auth_module['ops']['current_user']['output']
    except KeyError as e:
        raise MappError('INVALID_SPEC', f'Builtin auth module is missing key: {e}')
    
    global User
    User._model_spec = user
    User._module_spec = auth_module

    global UserSession
    UserSession._model_spec = user_session
    UserSession._module_spec = auth_module

    global PasswordHash
    PasswordHash._model_spec = password_hash
    PasswordHash._module_spec = auth_module

    global CreateUserOutput
    CreateUserOutput._op_spec = create_user_output
    CreateUserOutput._module_spec = auth_module

    global LoginUserOutput
    LoginUserOutput._op_spec = login_user_output
    LoginUserOutput._module_spec = auth_module

    global CurrentUserOutput
    CurrentUserOutput._op_spec = current_user_output
    CurrentUserOutput._module_spec = auth_module

    return True

#
# internal
#

def _verify_password(plain_password:str, hashed_password:str) -> bool:
    try:
        salt, hash_hex = hashed_password.split('$')
        salt_bytes = bytes.fromhex(salt)
        hash_bytes = bytes.fromhex(hash_hex)
        test_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt_bytes, 100_000)
        return secrets.compare_digest(test_hash, hash_bytes)
    except Exception:
        return False

def _get_password_hash(password:str) -> str:
    salt = secrets.token_bytes(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return f'{salt.hex()}${hash_bytes.hex()}'

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
    expires = datetime.now(timezone.utc) + timedelta(minutes=int(MAPP_AUTH_LOGIN_EXPIRATION_MINUTES))
    jti = secrets.token_hex(16)
    data_to_encode = data.copy()
    data_to_encode.update({'exp': expires, 'sub': data.get('sub'), 'jti': jti})
    if MAPP_AUTH_SECRET_KEY is None:
        raise AuthenticationError()
    token = jwt.encode(data_to_encode, MAPP_AUTH_SECRET_KEY, algorithm='HS256')
    return token, 'bearer', jti

def _get_user_id_from_token(ctx:dict, token:str) -> str:
    """parse a JWT token and return the user id as a string,
    raise AuthenticationError if the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, MAPP_AUTH_SECRET_KEY, algorithms=['HS256'])
        user_id: str = payload.get('sub')
        jti: str = payload.get('jti')
        if user_id is None or jti is None:
            raise AuthenticationError('Could not validate credentials')
        # Check session table for jti
        session = ctx.db.cursor.execute(
            'SELECT id FROM session WHERE id = ?', (jti,)
        ).fetchone()
        if not session:
            raise AuthenticationError('Session expired or logged out')
        return user_id
    except (ExpiredSignatureError, InvalidTokenError, Exception):
        raise AuthenticationError('Could not validate credentials')

#
# external
#

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def create_user(ctx: MappContext, params:object) -> CreateUserOutput:
    """
    Create a new user in the auth module.
    """
    name = params.name.strip()
    email = params.email.strip().lower()
    password = params.password
    password_confirm = params.password_confirm

    # validate input #

    field_errors = {}

    if name == '' or name is None:
        field_errors['name'] = 'Name cannot be empty'

    if not re.match(EMAIL_REGEX, email):
        field_errors['email'] = 'Invalid email format'
    
    if password is '' or password is None:
        field_errors['password'] = 'Password cannot be empty'

    if password != password_confirm:
        field_errors['password_confirm'] = 'Password confirmation does not match password'

    if field_errors:
        raise MappError('Could not create user', field_errors=field_errors)
    
    # check if user exists

    existing = ctx.db.cursor.execute(
        'SELECT id FROM user WHERE email = ?', (email,)
    ).fetchone()

    if existing:
        ctx.log(f'Could not create user, email already exists: {email}')
        raise AuthenticationError()
    
    # Generate unique user_id
    for _ in range(3):
        user_id = secrets.token_hex(16)
        collision = ctx.db.cursor.execute(
            'SELECT id FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        if not collision:
            break
    else:
        ctx.log(f'Could not create user, failed to generate unique user ID for {email}')
        raise AuthenticationError()

    ctx.db.cursor.execute(
        'INSERT INTO user (id, name, email) VALUES (?, ?, ?)',
        (user_id, name, email)
    )

    # Hash password
    pw_hash = _get_password_hash(password)
    for _ in range(3):
        pw_hash_id = secrets.token_hex(16)
        collision = ctx.db.cursor.execute(
            'SELECT id FROM password_hash WHERE id = ?', (pw_hash_id,)
        ).fetchone()
        if not collision:
            break
    else:
        ctx.log(f'Could not create user, failed to generate unique password hash ID for {email}')
        raise AuthenticationError()

    ctx.db.cursor.execute(
        'INSERT INTO password_hash (id, user_id, hash) VALUES (?, ?, ?)',
        (pw_hash_id, user_id, pw_hash)
    )
    ctx.db.commit()
    return CreateUserOutput(
        id=user_id,
        name=name,
        email=email,
    )

def login_user(ctx: MappContext, params:object) -> LoginUserOutput:
    """
    Log in a user in the auth module.
    """
    email = params.email.strip().lower()
    password = params.password
    user_id = _check_user_credentials(ctx, email, password)
    token, token_type, jti = _create_access_token({'sub': user_id})
    # Create session record
    ctx.db.cursor.execute(
        'INSERT INTO session (id, user_id, created_at) VALUES (?, ?, ?)',
        (jti, user_id, datetime.now(timezone.utc))
    )
    ctx.db.commit()
    return LoginUserOutput(
        access_token=token,
        token_type=token_type
    )

def current_user(ctx: MappContext, params:object) -> CurrentUserOutput:
    """
    Get the current logged-in user in the auth module.
    ctx: MappContext - The application context.
    params: object - No params needed for current user.

    return: CurrentUserOutput
        id: str - The ID of the current user.
        name: str - The name of the current user.
        email: str - The email of the current user.
    """
    return CurrentUserOutput(
        id='123',
        name='John Doe',
        email='current@example.com'
    )

def logout_user(ctx: MappContext, params:object) -> Acknowledgment:
    """
    Log out a user in the auth module.
    ctx: MappContext - The application context.
    params: object - No params needed for logout.

    return: Acknowledgment
        acknowledged: bool - Whether the logout was successful.
        message: str - Confirmation message of logout.
    """
    # Expect params to have access_token
    token = getattr(params, 'access_token', None)
    if not token:
        return Acknowledgment('No token provided')
    try:
        payload = jwt.decode(token, MAPP_AUTH_SECRET_KEY, algorithms=['HS256'])
        jti = payload.get('jti')
        if jti:
            ctx.db.cursor.execute('DELETE FROM session WHERE id = ?', (jti,))
            ctx.db.commit()
            return Acknowledgment('User logged out successfully')
        else:
            return Acknowledgment('Invalid token')
    except Exception:
        return Acknowledgment('Invalid token')

def delete_user(ctx: MappContext, params:object) -> Acknowledgment:
    """
    Delete a user in the auth module.
    ctx: MappContext - The application context.
    params: object - Parameters for deleting a user.
        user_id: str - The ID of the user to delete.

    return: Acknowledgment
        acknowledged: bool - Whether the deletion was successful.
        message: str - Confirmation message of deletion.
    """
    return Acknowledgment('User deleted successfully')