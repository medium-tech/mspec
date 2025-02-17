import json

from copy import copy
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

from core.types import to_json, metadata, email_regex, entity

__all__ = [
    'user',
    'user_session_to_json',
    'user_session_from_json',
    'user_session_validate',
    'access_token',
    'new_password',
    'create_user_form',
    'user_password_hash',
    'profile',
    'acl_to_json',
    'acl_from_json',
    'acl_validate',
    'acl_entry_to_json',
    'acl_entry_from_json',
    'acl_entry_validate'
]

# user #

@dataclass
class user:
    name: str
    email: str

    profile: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        self.email = self.email.lower()
    
    def validate(self):
        if not isinstance(self.id, str) and self.id is not None:
            raise ValueError('invalid user id')
        
        if not isinstance(self.name, str):
            raise ValueError('user name must be a string')
        
        if not email_regex.fullmatch(self.email):
            raise ValueError('user email is invalid')
        
        if not isinstance(self.profile, str) and self.profile is not None:
            raise ValueError('invalid user profile')
        
        return self
    
    def to_dict(self):
        data = asdict(self)
        if self.id is None:
            del data['id']
        if self.profile is None:
            del data['profile']
        return data
        
    def to_json(self):
        return to_json(self.to_dict())
    
    @classmethod
    def from_json(cls, user_json:str):
        return cls(**json.loads(user_json))
    
    @classmethod
    def example(cls):
        return cls(
            name='Alice',
            email='alice@nice.com',
            profile='12345'
        )

# user session #

def user_session_to_json(user_session:dict) -> str:
    return to_json(user_session)

def user_session_from_json(user_session_json:str) -> dict:
    return json.loads(user_session_json)

def user_session_validate(user_session:dict) -> dict:
    if not isinstance(user_session, dict):
        raise TypeError('user_session must be a dictionary')
    
    try:
        if not isinstance(user_session['id'], str):
            raise ValueError('user_session id must be a string')
    except KeyError:
        pass
    
    try:
        if not isinstance(user_session['user'], str):
            raise ValueError('user_session user must be a str')
        
    except KeyError:
        raise ValueError('user_session is missing user')
    
    try:
        if not isinstance(user_session['session_id'], str):
            raise ValueError('user_session session_id must be a string')
    except KeyError:
        raise ValueError('user_session is missing session_id')
    
    try:
        if not isinstance(user_session['expires'], datetime):
            raise ValueError('user_session expires must be a datetime object')
    except KeyError:
        raise ValueError('user_session is missing expires')
    
    if len(user_session.keys()) > 4:
        raise ValueError('user_session has too many keys')
    
    return user_session

# access token #

@dataclass
class access_token:
    access_token: str
    token_type: str

# new password #

@dataclass
class new_password:
    password1: str
    password2: str

    def validate(self):
        if self.password1 != self.password2:
            raise ValueError('new_password passwords do not match')
        
        if len(self.password1) < 8:
            raise ValueError('new_password password must be at least 8 characters')
        
        if not isinstance(self.password1, str):
            raise ValueError('new_password password1 must be a string')
        
        if not isinstance(self.password2, str):
            raise ValueError('new_password password2 must be a string')
        
        return self
    
@dataclass
class create_user_form:
    name: str
    email: str
    password: new_password

    def __post_init__(self):
        self.email = self.email.lower()
        if isinstance(self.password, dict):
            self.password = new_password(**self.password)

    def validate(self) :
        if not isinstance(self.name, str):
            raise ValueError('create_user_form name must be a string')
        if not isinstance(self.email, str):
            raise ValueError('create_user_form email must be a string')
        if not email_regex.fullmatch(self.email):
            raise ValueError('create_user_form email is invalid')
        self.password.validate()
        
        return self
    
    def to_dict(self) -> dict:
        return asdict(self)
        
    def to_json(self) -> str:
        return to_json(self.to_dict())
    
    @classmethod
    def from_json(cls, json_string:str) -> 'create_user_form':
        return cls(**json.loads(json_string))

    @classmethod
    def example(cls) -> 'create_user_form':
        return cls(
            name='Test User',
            email='my@email.com',
            password=new_password(
                password1='my-test-password',
                password2='my-test-password'
            )
        )

# user password hash #

@dataclass
class user_password_hash:

    user: str
    hash: str

    id: Optional[str] = None
    
    def validate(self):
        if not isinstance(self.id, str) and self.id is not None:
            raise ValueError('invalid user_password_hash id')
        
        if not isinstance(self.user, str):
            raise ValueError('user_password_hash user must be a string')
        
        if not isinstance(self.hash, str):
            raise ValueError('user_password_hash hash must be a string')
        
        return self
    
    def to_dict(self):
        data = asdict(self)
        if self.id is None:
            del data['id']
        return data
        
    def to_json(self):
        return to_json(self.to_dict())
    
    @classmethod
    def from_json(cls, user_password_hash_json:str):
        return cls(**json.loads(user_password_hash_json))
    
    @classmethod
    def example(cls):
        return cls(
            user='12345',
            hash='abc123',
            salt='def456'
        )

# profile #

@dataclass
class profile:

    name: str
    bio: str
    meta: metadata

    id: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.meta, dict):
            self.meta = metadata(**self.meta)
    
    def validate(self):
        if not isinstance(self.id, str) and self.id is not None:
            raise ValueError('invalid profile id')
        
        if not isinstance(self.name, str):
            raise ValueError('profile name must be a string')
        
        if not isinstance(self.bio, str):
            raise ValueError('profile bio must be a string')
        
        if not isinstance(self.meta, metadata):
            raise ValueError('profile meta must be a metadata object')
        
        self.meta.validate()
        
        return self
    
    def to_dict(self):
        data = asdict(self)
        if self.id is None:
            del data['id']
        return data
        
    def to_json(self):
        return to_json(self.to_dict())
    
    @classmethod
    def from_json(cls, profile_json:str):
        return cls(**json.loads(profile_json))
    
    @classmethod
    def example(cls):
        return cls(
            name='Alice',
            bio='Alice is a nice person.',
            meta=metadata(
                data={'age': 30},
                tags=['nice', 'friendly', 'guitar', 'drums', 'camera', 'film'],
                hierarchies=['artist/musician', 'artist/photographer']
            )
        )
    
# acl #

def acl_to_json(acl:dict) -> str:
    return to_json(acl)

def acl_from_json(acl_json:str) -> dict:
    return json.loads(acl_json)

def acl_validate(acl:dict) -> dict:
    if not isinstance(acl, dict):
        raise TypeError('acl must be a dictionary')
    
    try:
        if not isinstance(acl['id'], str):
            raise ValueError('acl id must be a string')
    except KeyError:
        pass
    
    try:
        if not isinstance(acl['name'], str):
            raise ValueError('acl name must be a string')
    except KeyError:
        raise ValueError('acl is missing name')
    
    try:
        if not isinstance(acl['admin'], str):
            raise ValueError('acl admin must be a str')
    except KeyError:
        raise ValueError('acl is missing admin')
    
    if len(acl.keys()) > 3:
        raise ValueError('acl has too many keys')
    
    return acl
    
# acl entry #

def acl_entry_to_json(acl_entry:dict) -> str:
    return to_json(acl_entry)

def acl_entry_from_json(acl_entry_json:str) -> dict:
    return json.loads(acl_entry_json)

def acl_entry_validate(acl_entry:dict) -> dict:
    if not isinstance(acl_entry, dict):
        raise TypeError('acl_entry must be a dictionary')
    
    try:
        if not isinstance(acl_entry['id'], str):
            raise ValueError('acl_entry id must be a string')
    except KeyError:
        pass
    
    try:
        if not isinstance(acl_entry['acl'], str):
            raise ValueError('acl must be a str')
    except KeyError:
        raise ValueError('acl_entry is missing acl')
    
    try:
        if not isinstance(acl_entry['entity'], entity):
            raise ValueError('acl_entry entity must be a str')
        
        acl_entry['entity'].validate()
        
    except KeyError:
        raise ValueError('acl_entry is missing permissions')
    
    if len(acl_entry.keys()) > 3:
        raise ValueError('acl_entry has too many keys')
    
    return acl_entry
