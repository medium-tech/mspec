import os

from core.db import db_read_user, db_create_user_password_hash, db_create_user
from core.exceptions import AuthenticationError, NotFoundError
from core.models import user, user_password_hash, profile, access_token, create_user_form
from datetime import datetime, timedelta, timezone
from typing import Annotated

from jose import jwt, JWTError
from passlib.context import CryptContext
from pymongo.collection import Collection
from bson import ObjectId


__all__ = [
    'verify_password',
    'get_password_hash',
    'login_user',
    'create_access_token',
    'create_new_user',
    'delete_user',
    'delete_profile'
]


MSTACK_AUTH_SECRET_KEY = os.environ.get('MSTACK_AUTH_SECRET_KEY')   # openssl rand -hex 32
MSTACK_AUTH_ALGORITHM = os.environ.get('MSTACK_AUTH_ALGORITHM', 'HS256')
MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES = os.environ.get('MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES', 60 * 24 * 7)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v0/core/auth/login')


def get_user_from_token(ctx:dict, token:str):
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


def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password:str) -> str:
    return pwd_context.hash(password)


def login_user(ctx:dict, email: str, password: str) -> access_token:
    users:Collection = ctx['db']['client']['msample']['core.user']

    user_db_result = users.find_one({'email': email.lower()})
    try:
        user_id = str(user_db_result['_id'])
    except AttributeError:
        """user_id is None - user id not found"""
        raise AuthenticationError('Invalid username or password')

    user_pw_hashes:Collection = ctx['db']['client']['msample']['core.user_password_hash']
    
    try:
        user_pw_db_result = user_pw_hashes.find_one({'user': ObjectId(user_id)})
    except IndexError:
        raise AuthenticationError('Invalid username or password')

    if not verify_password(password, user_pw_db_result['hash']):
        raise AuthenticationError('Invalid username or password')
    
    return create_access_token(data={'sub': str(user_id)})


def create_access_token(data: dict):
    expires = datetime.now(timezone.utc) + timedelta(minutes=MSTACK_AUTH_LOGIN_EXPIRATION_MINUTES)

    data_to_encode = data.copy()
    data_to_encode.update({'exp': expires})

    if MSTACK_AUTH_SECRET_KEY is None:
        raise ValueError('MSTACK_AUTH_SECRET_KEY not set')

    token = jwt.encode(data_to_encode, MSTACK_AUTH_SECRET_KEY, algorithm=MSTACK_AUTH_ALGORITHM)
    return access_token(access_token=token, token_type='bearer')


def create_new_user(ctx:dict, data:create_user_form) -> user:
    users:Collection = ctx['db']['client']['msample']['core.user']

    if users.find_one({'email': data.email}) is not None:
        raise AuthenticationError('Email already registered')

    new_user = user(name=data.name, email=data.email)
    new_user = db_create_user(ctx, new_user)

    hash = user_password_hash(user=new_user.id, hash=get_password_hash(data.password.password1))
    hash = db_create_user_password_hash(ctx, hash)

    return new_user
