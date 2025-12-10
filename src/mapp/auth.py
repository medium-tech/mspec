import os
import re
import time
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from mapp.context import MappContext, MAPP_APP_PATH
from mapp.errors import AuthenticationError, MappError, MappValidationError
from mapp.types import (
    Acknowledgment,
    User,
    UserSession,
    PasswordHash,
    CreateUserOutput,
    LoginUserOutput,
    CurrentUserOutput
)

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

def _verify_root_password(user_input:str) -> str:
    root_pw_file = MAPP_APP_PATH / '.mapp-root-password'
    try:
        with open(root_pw_file, 'r', encoding='utf-8') as f:
            stored_password = f.read().strip()
    except FileNotFoundError:
        raise AuthenticationError('Root password file not found')

    if user_input != stored_password:
        raise AuthenticationError('Could not authenticate')
    
    return stored_password

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

    err_msg = 'Invalid email or password'
    
    user_id_result = ctx.db.cursor.execute(
        "SELECT id FROM user WHERE email = ?",
        (email.lower(),)
    ).fetchone()

    if user_id_result is None:
        raise AuthenticationError(err_msg)
    
    pw_hash_result = ctx.db.cursor.execute(
        "SELECT hash FROM password_hash WHERE user_id = ?", 
        (user_id_result[0],)
    ).fetchone()

    if pw_hash_result is None:
        raise AuthenticationError(err_msg)

    if not _verify_password(password, pw_hash_result[0]):
        raise AuthenticationError(err_msg)
    
    return str(user_id_result[0])

def _create_access_token(user_id: str) -> tuple[str, str, int]:

    """
    Create an access token for a user.

    args ::
        data :: dict containing the user id as 'sub' key

    return :: tuple of (token:str, token_type:str, jti:int)
        token - str - The JWT access token with the following fields
            sub - str - The subject (user id).
            exp - int - The expiration time as a Unix timestamp.
            jti - int - The unique identifier for the token.
        token_type - str - The type of the token, e.g., 'bearer'.
        jti - int - The unique identifier for the token.

    raises :: AuthenticationError
    """

    expires = datetime.now(timezone.utc) + timedelta(minutes=int(MAPP_AUTH_LOGIN_EXPIRATION_MINUTES))
    jti = secrets.randbits(63)
    data_to_encode = {'sub': user_id, 'exp': expires, 'jti': str(jti)}
    if MAPP_AUTH_SECRET_KEY is None:
        raise AuthenticationError()
    token = jwt.encode(data_to_encode, MAPP_AUTH_SECRET_KEY, algorithm='HS256')
    return token, 'bearer', jti

def _parse_access_token(ctx:dict, token:str) -> tuple[User, str]:
    """
    Parse and validate an access token, returning the associated User.
    if session is invalid or expired, raises AuthenticationError.
    """
    try:
        payload = jwt.decode(token, MAPP_AUTH_SECRET_KEY, algorithms=['HS256'])
        user_id: str = payload['sub']
        jti: str = payload['jti']
        exp: int = payload['exp']
    except Exception as e:
        ctx.log(f'Caught exception decoding access token: {e.__class__.__name__}: {e}')
        raise AuthenticationError('Invalid access token')
    
    # check if token expired #
        
    if time.time() > exp:

        ctx.db.cursor.execute(
            'DELETE FROM user_session WHERE id = ? AND user_id = ?',
            (jti, user_id)
        )
        ctx.db.commit()

        raise AuthenticationError('Session has expired')
    
    # check session exists #

    session_result = ctx.db.cursor.execute(
        'SELECT id FROM user_session WHERE id = ? AND user_id = ?',
        (jti, user_id)
    ).fetchone()

    if session_result is None:
        raise AuthenticationError('Invalid session token')
    
    # load user #

    user_result = ctx.db.cursor.execute(
        'SELECT id, name, email FROM user WHERE id = ?',
        (user_id,)
    ).fetchone()

    user = User(
        id=str(user_result[0]),
        name=user_result[1],
        email=user_result[2]
    )

    return user, jti
#
# external
#

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def create_user(ctx: MappContext, params:object) -> CreateUserOutput:
    err_msg = 'Could not create user'

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
    
    if password == '' or password is None:
        field_errors['password'] = 'Password cannot be empty'

    if password != password_confirm:
        field_errors['password_confirm'] = 'Password confirmation does not match password'

    if field_errors:
        raise MappValidationError(err_msg, field_errors)
    
    # check if user exists

    existing = ctx.db.cursor.execute(
        'SELECT id FROM user WHERE email = ?', (email,)
    ).fetchone()

    if existing:
        ctx.log(f'Could not create user, email already exists: {email}')
        raise AuthenticationError(err_msg)
    
    # Generate unique user_id
    for _ in range(3):
        user_id = secrets.randbits(63)
        collision = ctx.db.cursor.execute(
            'SELECT id FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        if not collision:
            break
    else:
        ctx.log(f'Could not create user, failed to generate unique user ID for {email}')
        raise AuthenticationError(err_msg)

    ctx.db.cursor.execute(
        'INSERT INTO user (id, name, email) VALUES (?, ?, ?)',
        (user_id, name, email)
    )

    # Hash password
    pw_hash = _get_password_hash(password)
    for _ in range(3):
        pw_hash_id = secrets.randbits(63)
        collision = ctx.db.cursor.execute(
            'SELECT id FROM password_hash WHERE id = ?', (pw_hash_id,)
        ).fetchone()
        if not collision:
            break
    else:
        ctx.log(f'Could not create user, failed to generate unique password hash ID for {email}')
        raise AuthenticationError(err_msg)

    ctx.db.cursor.execute(
        'INSERT INTO password_hash (id, user_id, hash) VALUES (?, ?, ?)',
        (pw_hash_id, user_id, pw_hash)
    )
    ctx.db.commit()
    return CreateUserOutput(
        id=str(user_id),
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
    token, token_type, jti = _create_access_token(user_id)
    # Create session record
    ctx.db.cursor.execute(
        'INSERT INTO user_session (id, user_id, created_at) VALUES (?, ?, ?)',
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
        number_of_sessions: int - The number of active sessions for the current user.
    """
    access_token = ctx.current_access_token()
    assert access_token is not None

    user, _jti = _parse_access_token(ctx, access_token)
    
    number_of_sessions = ctx.db.cursor.execute(
        'SELECT COUNT(*) FROM user_session WHERE user_id = ?', (user.id,)
    ).fetchone()[0]

    return CurrentUserOutput(
        id=user.id,
        name=user.name,
        email=user.email,
        number_of_sessions=number_of_sessions
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

    # get current user #

    access_token = ctx.current_access_token()
    assert access_token is not None

    user, jti = _parse_access_token(ctx, access_token)

    match params.mode:
        case 'current':
            sql = 'DELETE FROM user_session WHERE id = ? AND user_id = ?'
            values = (jti, user.id)
            msg = 'Current session logged out successfully'
        
        case 'others':
            sql = 'DELETE FROM user_session WHERE user_id = ? AND id != ?'
            values = (user.id, jti)
            msg = 'Other sessions logged out successfully'
        
        case 'all':
            sql = 'DELETE FROM user_session WHERE user_id = ?'
            values = (user.id,)
            msg = 'All sessions logged out successfully'
        
        case _:
            # shouldn't get here due to param validation
            raise MappError('INVALID_LOGOUT_MODE', f'Unknown logout mode: {params.mode}')
        
    ctx.db.cursor.execute(sql, values)
    ctx.db.commit()
    return Acknowledgment(msg)
        
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

    # get current user #

    access_token = ctx.current_access_token()
    assert access_token is not None

    user, jti = _parse_access_token(ctx, access_token)

    # delete all sessions for this user #

    ctx.db.cursor.execute(
        'DELETE FROM user_session WHERE user_id = ?', (user.id,)
    )

    # delete user record #
    
    ctx.db.cursor.execute(
        'DELETE FROM user WHERE id = ?', (user.id,)
    )
    ctx.db.commit()
    return Acknowledgment('User deleted successfully')

def drop_sessions(ctx: MappContext, params:object) -> Acknowledgment:
    """
    Drop all user sessions for all users
    ctx: MappContext - The application context.
    params: object - No params needed for dropping sessions.
    return: Acknowledgment
        acknowledged: bool - Whether the operation was successful.
        message: str - Confirmation message of operation.
    """

    _verify_root_password(params.root_password)

    ctx.db.cursor.execute(
        'DELETE FROM user_session'
    )
    ctx.db.commit()
    return Acknowledgment('All sessions dropped successfully')
