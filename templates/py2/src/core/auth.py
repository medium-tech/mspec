import os
import sqlite3

from core.db import db_read_user, db_create_user
from core.exceptions import AuthenticationError, NotFoundError, ForbiddenError
from core.models import User, UserPasswordHash, AccessToken, CreateUser
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext


__all__ = [
    'create_new_user',
    'login_user'
]


MSTACK_AUTH_SECRET_KEY = os.environ.get('MSTACK_AUTH_SECRET_KEY')   # openssl rand -hex 32
MSTACK_AUTH_ALGORITHM = os.environ.get('MSTACK_AUTH_ALGORITHM', 'HS256')
MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES = os.environ.get('MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES', 60 * 24 * 7)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def _get_user_from_token(ctx:dict, token:str):
    try:
        payload = jwt.decode(token, MSTACK_AUTH_SECRET_KEY, algorithms=[MSTACK_AUTH_ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise AuthenticationError('Could not validate credentials')
        
    except JWTError:
        raise AuthenticationError('Could not validate credentials')
    
    try:
        return db_read_user(ctx, user_id)
    except NotFoundError:
        raise AuthenticationError('Could not validate credentials')

def _verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _get_password_hash(password:str) -> str:
    return pwd_context.hash(password)

def _check_user_credentials(ctx: dict, email: str, password: str) -> str:
    """
    returns user id if credentials are valid, else raises AuthenticationError

    args ::
        ctx :: dict containing the database client
        email :: user email
        password :: user password
    
    return :: str of user id
    raises :: AuthenticationError
    """
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    user_id_result = cursor.execute(
        "SELECT id FROM user WHERE email = ?",
        (email.lower(),)
    ).fetchone()

    if user_id_result is None:
        raise AuthenticationError('Invalid username or password')
    
    pw_hash_result = cursor.execute(
        "SELECT hash FROM user_password_hash WHERE user_id = ?", 
        (user_id_result[0],)
    ).fetchone()

    if pw_hash_result is None:
        raise AuthenticationError('Invalid username or password')

    if not _verify_password(password, pw_hash_result[0]):
        raise AuthenticationError('Invalid username or password')
    
    return str(user_id_result[0])

def _create_access_token(data: dict):
    expires = datetime.now(timezone.utc) + timedelta(minutes=MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES)

    data_to_encode = data.copy()
    data_to_encode.update({'exp': expires})

    if MSTACK_AUTH_SECRET_KEY is None:
        raise ValueError('MSTACK_AUTH_SECRET_KEY not set')

    token = jwt.encode(data_to_encode, MSTACK_AUTH_SECRET_KEY, algorithm=MSTACK_AUTH_ALGORITHM)
    return AccessToken(access_token=token, token_type='bearer')

#
# external methods
#

def create_new_user(ctx:dict, incoming_user:CreateUser) -> User:

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    user_id_result = cursor.execute(
        "SELECT id FROM user WHERE email = ?",
        (incoming_user.email,)
    ).fetchone()

    if user_id_result is not None:
        raise ForbiddenError('Email already registered')

    created_user = db_create_user(ctx, incoming_user.get_user_obj())

    pw_hash = UserPasswordHash(user_id=created_user.id, hash=_get_password_hash(incoming_user.password1))
    pw_hash.validate()
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute("INSERT INTO user_password_hash(user_id, hash) VALUES(?, ?)", (pw_hash.user_id, pw_hash.hash))
    assert result.rowcount == 1

    ctx['db']['commit']()

    return created_user

def login_user(ctx:dict, email: str, password: str) -> AccessToken:
    user_id = _check_user_credentials(ctx, email, password)
    print(f'login_user: {user_id} {type(user_id)}')
    assert isinstance(user_id, str)
    assert user_id != ''
    return _create_access_token(data={'sub': str(user_id)})