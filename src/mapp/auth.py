import os
import re
import time
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from mapp.context import MappContext, MAPP_APP_PATH
from mapp.errors import AuthenticationError, MappError, MappValidationError
from mapp.types import (
    Acknowledgment,
    User,
    UserSession,
    PasswordHash,
    LoginUserOutput,
    CurrentUserOutput
)

MAPP_AUTH_SECRET_KEY = os.environ.get('MAPP_AUTH_SECRET_KEY')   # openssl rand -hex 32
MAPP_AUTH_LOGIN_EXPIRATION_MINUTES = os.environ.get('MAPP_AUTH_LOGIN_EXPIRATION_MINUTES', 60 * 24 * 7)

__all__ = [
    'User',
    'PasswordHash',
    'create_user',
    'login_user',
    'current_user',
    'logout_user',
    'delete_user',
    'drop_sessions'
]

#
# internal
#

ROOT_PASSWORD_HASH_FILE = MAPP_APP_PATH / '.mapp-root-password'

def _verify_root_password(user_input:str) -> bool:
    """returns True if root password is correct, else raises AuthenticationError"""

    try:
        with open(ROOT_PASSWORD_HASH_FILE, 'r', encoding='utf-8') as f:
            root_pw_hash = f.read().strip()
    except FileNotFoundError:
        raise AuthenticationError('Root password file not found')

    if not _verify_password(user_input, root_pw_hash):
        raise AuthenticationError('Invalid root password')
    
    return True

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

def create_user(ctx: MappContext, name: str, email: str, password: str, password_confirm: str) -> dict:
    err_msg = 'Could not create user'

    """
    Create a new user in the auth module.
    """
    name = name.strip()
    email = email.strip().lower()
    password = password
    password_confirm = password_confirm

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
        raise AuthenticationError(err_msg + ': email already exists')
    
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
        raise AuthenticationError(err_msg + ': failed to generate unique user ID')

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
        raise AuthenticationError(err_msg + ': failed to generate unique password hash ID')

    ctx.db.cursor.execute(
        'INSERT INTO password_hash (id, user_id, hash) VALUES (?, ?, ?)',
        (pw_hash_id, user_id, pw_hash)
    )
    ctx.db.commit()

    return {
        'type': 'struct',
        'value': {
            'id': str(user_id),
            'name': name,
            'email': email
        }
    }

def login_user(ctx: MappContext, email_or_params, password: str = None):
    """
    Log in a user in the auth module.
    Supports both old-style (params object) and new-style (explicit args) calling conventions.
    """
    # Handle both old and new calling conventions
    if hasattr(email_or_params, 'email'):
        # Old style: params object
        email = email_or_params.email.strip().lower()
        password = email_or_params.password
        use_old_format = True
    else:
        # New style: explicit args
        email = email_or_params.strip().lower()
        use_old_format = False
    
    user_id = _check_user_credentials(ctx, email, password)
    token, token_type, jti = _create_access_token(user_id)
    # Create session record
    ctx.db.cursor.execute(
        'INSERT INTO user_session (id, user_id, created_at) VALUES (?, ?, ?)',
        (jti, user_id, datetime.now(timezone.utc))
    )
    ctx.db.commit()
    
    if use_old_format:
        return LoginUserOutput(
            access_token=token,
            token_type=token_type
        )
    else:
        return {
            'type': 'struct',
            'value': {
                'access_token': token,
                'token_type': token_type
            }
        }

def current_user(ctx: MappContext, *args):
    """
    Get the current logged-in user in the auth module.
    Supports both old-style (params object) and new-style (no second param) calling conventions.
    
    ctx: MappContext - The application context.
    args: For old-style calls, contains (params,). For new-style, empty.

    return: CurrentUserOutput (old style) or dict (new style)
        id: str - The ID of the current user.
        name: str - The name of the current user.
        email: str - The email of the current user.
        number_of_sessions: int - The number of active sessions for the current user.
    """
    # When called from the old deprecated path: current_user(ctx, params) or current_user(ctx, None)
    # When called from lingo: current_user(ctx)
    use_old_format = len(args) > 0
    
    access_token = ctx.current_access_token()
    
    if access_token is None or access_token == '':
        raise AuthenticationError('Not logged in')

    user, _jti = _parse_access_token(ctx, access_token)
    
    number_of_sessions = ctx.db.cursor.execute(
        'SELECT COUNT(*) FROM user_session WHERE user_id = ?', (user.id,)
    ).fetchone()[0]

    if use_old_format:
        return CurrentUserOutput(
            id=user.id,
            name=user.name,
            email=user.email,
            number_of_sessions=number_of_sessions
        )
    else:
        return {
            'type': 'struct',
            'value': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'number_of_sessions': number_of_sessions
            }
        }

def logout_user(ctx: MappContext, mode_or_params, *args):
    """
    Log out a user in the auth module.
    Supports both old-style (params object) and new-style (explicit args) calling conventions.
    
    ctx: MappContext - The application context.
    mode_or_params: str or object - Mode for new-style calls, or params object for old-style
    args: Empty for both styles

    return: Acknowledgment (old style) or dict (new style)
        acknowledged: bool - Whether the logout was successful.
        message: str - Confirmation message of logout.
    """
    # Handle both old and new calling conventions
    if hasattr(mode_or_params, 'mode'):
        # Old style: params object
        mode = mode_or_params.mode
        use_old_format = True
    else:
        # New style: explicit args
        mode = mode_or_params
        use_old_format = False

    # get current user #

    access_token = ctx.current_access_token()
    assert access_token is not None

    user, jti = _parse_access_token(ctx, access_token)

    match mode:
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
            raise MappError('INVALID_LOGOUT_MODE', f'Unknown logout mode: {mode}')
        
    ctx.db.cursor.execute(sql, values)
    ctx.db.commit()
    
    if use_old_format:
        return Acknowledgment(msg)
    else:
        return {
            'type': 'struct',
            'value': {
                'acknowledged': True,
                'message': msg
            }
        }
        
def delete_user(ctx: MappContext, *args):
    """
    Delete a user in the auth module.
    Supports both old-style (params object) and new-style (no second param) calling conventions.
    
    ctx: MappContext - The application context.
    args: For old-style calls, contains (params,). For new-style, empty.

    return: Acknowledgment (old style) or dict (new style)
        acknowledged: bool - Whether the deletion was successful.
        message: str - Confirmation message of deletion.
    """
    # When called from the old deprecated path: delete_user(ctx, params) or delete_user(ctx, None)
    # When called from lingo: delete_user(ctx)
    use_old_format = len(args) > 0

    # get current user #

    access_token = ctx.current_access_token()
    if access_token is None:
        raise AuthenticationError('Not logged in')

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
    
    if use_old_format:
        return Acknowledgment('User deleted successfully')
    else:
        return {
            'type': 'struct',
            'value': {
                'acknowledged': True,
                'message': 'User deleted successfully'
            }
        }

def drop_sessions(ctx: MappContext, root_password_or_params, *args):
    """
    Drop all user sessions for all users.
    Supports both old-style (params object) and new-style (explicit args) calling conventions.
    
    ctx: MappContext - The application context.
    root_password_or_params: str or object - Root password for new-style, or params object for old-style
    args: Empty for both styles
    
    return: Acknowledgment (old style) or dict (new style)
        acknowledged: bool - Whether the operation was successful.
        message: str - Confirmation message of operation.
    """
    # Handle both old and new calling conventions
    if hasattr(root_password_or_params, 'root_password'):
        # Old style: params object
        root_password = root_password_or_params.root_password
        use_old_format = True
    else:
        # New style: explicit args
        root_password = root_password_or_params
        use_old_format = False

    assert _verify_root_password(root_password) is True

    ctx.db.cursor.execute(
        'DELETE FROM user_session'
    )
    ctx.db.commit()
    
    if use_old_format:
        return Acknowledgment('All sessions dropped successfully')
    else:
        return {
            'type': 'struct',
            'value': {
                'acknowledged': True,
                'message': 'All sessions dropped successfully'
            }
        }
