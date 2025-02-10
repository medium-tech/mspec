import json
from datetime import datetime
from . types import to_json, meta, email_regex, entity

__all__ = [
    'user_to_json',
    'user_from_json',
    'user_validate',
    'user_session_to_json',
    'user_session_from_json',
    'user_session_validate',
    'user_password_hash_to_json',
    'user_password_hash_from_json',
    'user_password_hash_validate',
    'profile_to_json',
    'profile_from_json',
    'profile_validate',
    'acl_to_json',
    'acl_from_json',
    'acl_validate',
    'acl_entry_to_json',
    'acl_entry_from_json',
    'acl_entry_validate'
]

# user #

def user_to_json(user:dict) -> str:
    return to_json(user)

def user_from_json(user_json:str) -> dict:
    return json.loads(user_json)

def user_validate(user:dict) -> dict:
    if not isinstance(user, dict):
        raise TypeError('user must be a dictionary')
    
    try:
        if not isinstance(user['id'], str):
            raise ValueError('user id must be a string')
        
    except KeyError:
        pass
    
    try:
        if not isinstance(user['name'], str):
            raise ValueError('user name must be a string')
    except KeyError:
        raise ValueError('user is missing name')
    
    try:
        if not email_regex.fullmatch(user['email']):
            raise ValueError('user email is invalid')
    
    except TypeError:
        raise ValueError('user email is invalid')

    except KeyError:
        raise ValueError('user is missing email')
    
    try:
        if not isinstance(user['profile'], str):
            raise ValueError('user profile must be a str')

    except KeyError:
        raise ValueError('user is missing profile')
    
    if len(user.keys()) > 4:
        raise ValueError('user has too many keys')
    
    return user

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
    
# user password hash #

def user_password_hash_to_json(user_password_hash:dict) -> str:
    return to_json(user_password_hash)

def user_password_hash_from_json(user_password_hash_json:str) -> dict:
    return json.loads(user_password_hash_json)

def user_password_hash_validate(user_password_hash:dict) -> dict:
    if not isinstance(user_password_hash, dict):
        raise TypeError('user_password_hash must be a dictionary')
    
    try:
        if not isinstance(user_password_hash['id'], str):
            raise ValueError('user_password_hash id must be a string')
    except KeyError:
        pass
    
    try:
        if not isinstance(user_password_hash['user'], str):
            raise ValueError('user_password_hash user must be a str')
    except KeyError:
        raise ValueError('user_password_hash is missing user')
    
    try:
        if not isinstance(user_password_hash['hash'], str):
            raise ValueError('user_password_hash hash must be a string')
    except KeyError:
        raise ValueError('user_password_hash is missing hash')
    
    try:
        if not isinstance(user_password_hash['salt'], str):
            raise ValueError('user_password_hash salt must be a string')
    except KeyError:
        raise ValueError('user_password_hash is missing salt')
    
    if len(user_password_hash.keys()) > 3:
        raise ValueError('user_password_hash has too many keys')
    
    return user_password_hash
    
# profile #

def profile_to_json(profile:dict) -> str:
    return to_json(profile)

def profile_from_json(profile_json:str) -> dict:
    return json.loads(profile_json)

def profile_validate(profile:dict) -> dict:
    if not isinstance(profile, dict):
        raise TypeError('profile must be a dictionary')
    
    try:
        if not isinstance(profile['id'], str):
            raise ValueError('profile id must be a string')
    except KeyError:
        pass
    
    try:
        if not isinstance(profile['name'], str):
            raise ValueError('profile name must be a string')
    except KeyError:
        raise ValueError('profile is missing name')
    
    try:
        if not isinstance(profile['bio'], str):
            raise ValueError('profile bio must be a string')
    except KeyError:
        raise ValueError('profile is missing bio')
    
    try:
        if not isinstance(profile['meta'], meta):
            raise ValueError('profile permissions must be a meta object')
        
        profile['meta'].validate()

    except KeyError:
        raise ValueError('profile is missing permissions')
    
    if len(profile.keys()) > 4:
        raise ValueError('profile has too many keys')
    
    return profile
    
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
