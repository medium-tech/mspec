import atexit

from core.models import *
from core.exceptions import NotFoundError

# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case", "Sample": "module.name.camel_case"}
from sample_module import sample_module_db
# end for ::

from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId


# vars :: {"mongodb://127.0.0.1:27017": "db.default_url", "MSpec": "project.name.camel_case"}

__all__ = [
    'create_db_context',

    'db_create_user',
    'db_read_user',
    'db_update_user',
    'db_delete_user',
    'db_list_user',

    'db_create_user_session',
    'db_read_user_session',
    'db_update_user_session',
    'db_delete_user_session',
    'db_list_user_session',

    'db_create_user_password_hash',
    'db_read_user_password_hash',
    'db_update_user_password_hash',
    'db_delete_user_password_hash',
    'db_list_user_password_hash',

    'db_create_profile',
    'db_read_profile',
    'db_update_profile',
    'db_delete_profile',
    'db_list_profile',

    'db_create_acl',
    'db_read_acl',
    'db_update_acl',
    'db_delete_acl',
    'db_list_acl',

    'db_create_acl_entry',
    'db_read_acl_entry',
    'db_update_acl_entry',
    'db_delete_acl_entry',
    'db_list_acl_entry'
]

def create_db_context(client:MongoClient=None) -> dict:
    """
    initialize the database client.

    args ::
        client :: the client to use, if None, a new client will be created with default settings.
    
    return :: None
    """
    if client is None:
        client = MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=3_000)

    atexit.register(client.close)

    return {'db': {'client': client}}

#
# model crud ops
#

# user #

def db_create_user(ctx:dict, obj:user) -> user:
    """
    create a user in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to create the user with.

    return :: user object
    """
    if obj.id is not None:
        raise ValueError('cannot use user with id to create new user')
    users:Collection = ctx['db']['client']['msample']['core.user']
    result = users.insert_one(obj.validate().to_dict())
    obj.id = str(result.inserted_id)
    return obj

def db_read_user(ctx:dict, id:str) -> user:
    """
    read a user from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user to read.
    
    return :: user object
    raises :: NotFoundError if the user does not exist
    """
    users:Collection = ctx['db']['client']['msample']['core.user']
    db_entry = users.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'user {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return user(**db_entry).validate()

def db_update_user(ctx:dict, obj:user) -> None:
    """
    update a user in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to update the user with.

    return :: None
    raises :: NotFoundError if the user does not exist
    """
    obj.validate()
    data = obj.to_dict()
    _id = data.pop('id')

    users:Collection = ctx['db']['client']['msample']['core.user']
    result = users.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'user {_id} not found')

def db_delete_user(ctx:dict, id:str) -> None:
    """
    delete a user from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user to delete.

    return :: None
    """
    users = ctx['db']['client']['msample']['core.user']
    users.delete_one({'_id': ObjectId(id)})

def db_list_user(ctx:dict, offset:int=0, limit:int=25) -> list[user]:
    """
    list users in the database.

    args ::
        ctx :: dict containing the database client

    return :: list of user objects
    """
    users = ctx['db']['client']['msample']['core.user']
    items = []
    for item in users.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(user(**item).validate())
    return items

# user session #

def db_create_user_session(ctx:dict, data:dict) -> dict:
    """
    create a user session in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the user session with.
    return :: dict of the created user session.
    """
    user_sessions = ctx['db']['client']['msample']['core.user_session']
    result = user_sessions.insert_one(user_session_validate(data))
    data['id'] = str(result.inserted_id)
    return data 

def db_read_user_session(ctx:dict, id:str) -> dict:
    """
    read a user session from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user session to read.
    
    return :: dict of the user session
    raises :: NotFoundError if the user session does not exist
    """
    user_sessions = ctx['db']['client']['msample']['core.user_session']
    db_entry = user_sessions.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'user session {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return user_session_validate(db_entry)

def db_update_user_session(ctx:dict, data:dict) -> None:
    """
    update a user session in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to update the user session with.

    return :: None
    raises :: NotFoundError if the user session does not exist
    """
    user_session_validate(data)
    _id = data.pop('id')
    user_sessions = ctx['db']['client']['msample']['core.user_session']
    result = user_sessions.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'user session {id} not found')

def db_delete_user_session(ctx:dict, id:str) -> None:
    """
    delete a user session from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user session to delete.

    return :: None
    """
    user_sessions = ctx['db']['client']['msample']['core.user_session']
    user_sessions.delete_one({'_id': ObjectId(id)})

def db_list_user_session(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list user sessions from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: list of all user sessions.
    """
    user_sessions = ctx['db']['client']['msample']['core.user_session']
    items = []
    for item in user_sessions.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(user_session_validate(item))
    return items

# user password hash #

def db_create_user_password_hash(ctx:dict, data:dict) -> dict:
    """
    create a user password hash in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the user password hash with.

    return :: dict of the created user password hash.
    """
    user_password_hashes = ctx['db']['client']['msample']['core.user_password_hash']
    result = user_password_hashes.insert_one(user_password_hash_validate(data))
    data['id'] = str(result.inserted_id)
    return data 

def db_read_user_password_hash(ctx:dict, id:str) -> dict:
    """
    read a user password hash from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user password hash to read.
    
    return :: dict of the user password hash
    raises :: NotFoundError if the user password hash does not exist
    """
    user_password_hashes = ctx['db']['client']['msample']['core.user_password_hash']
    db_entry = user_password_hashes.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'user password hash {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return user_password_hash_validate(db_entry)
    
def db_update_user_password_hash(ctx:dict, data:dict) -> None:
    """
    update a user password hash in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to update the user password hash with.

    return :: None
    raises :: NotFoundError if the user password hash does not exist
    """
    user_password_hash_validate(data)
    _id = data.pop('id')
    user_password_hashes = ctx['db']['client']['msample']['core.user_password_hash']
    result = user_password_hashes.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'user password hash {id} not found')

def db_delete_user_password_hash(ctx:dict, id:str) -> None:
    """
    delete a user password hash from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user password hash to delete.

    return :: None
    """
    user_password_hashes = ctx['db']['client']['msample']['core.user_password_hash']
    user_password_hashes.delete_one({'_id': ObjectId(id)})

def db_list_user_password_hash(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list user password hashes from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of dicts of all user password hashes.
    """
    user_password_hashes = ctx['db']['client']['msample']['core.user_password_hash']
    items = []
    for item in user_password_hashes.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(user_password_hash_validate(item))
    return items

# profile #

def db_create_profile(ctx:dict, obj:profile) -> profile:
    """
    create a profile in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to create the profile with.

    return :: profile object with new id
    """
    profiles:Collection = ctx['db']['client']['msample']['core.profile']
    result = profiles.insert_one(obj.validate().to_dict())
    obj.id = str(result.inserted_id)
    return obj 

def db_read_profile(ctx:dict, id:str) -> profile:
    """
    read a profile from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the profile to read.
    
    return :: profile object if it exists
    raises :: NotFoundError if the profile does not exist
    """
    profiles:Collection = ctx['db']['client']['msample']['core.profile']
    db_entry = profiles.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'profile {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return profile(**db_entry).validate()
    
def db_update_profile(ctx:dict, obj:profile) -> None:
    """
    update a profile in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to update the profile with.

    return :: None
    raises :: NotFoundError if the profile does not exist
    """
    obj.validate()
    data = obj.to_dict()
    _id = data.pop('id')

    profiles:Collection = ctx['db']['client']['msample']['core.profile']
    result = profiles.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'profile {_id} not found')
    
def db_delete_profile(ctx:dict, id:str) -> None:
    """
    delete a profile from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the profile to delete.

    return :: None
    """
    profiles = ctx['db']['client']['msample']['core.profile']
    profiles.delete_one({'_id': ObjectId(id)})

def db_list_profile(ctx:dict, offset:int=0, limit:int=25) -> list[profile]:
    """
    list profiles from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: list of profile objects.
    """
    profiles = ctx['db']['client']['msample']['core.profile']
    items = []
    for item in profiles.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(profile(**item).validate())
    return items

# acl #

def db_create_acl(ctx:dict, data:dict) -> dict:
    """
    create a acl in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the acl with.

    return :: dict of the created acl.
    """
    acls = ctx['db']['client']['msample']['core.acl']
    result = acls.insert_one(acl_validate(data))
    data['id'] = str(result.inserted_id)
    return data 

def db_read_acl(ctx:dict, id:str) -> dict:
    """
    read a acl from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the acl to read.
    
    return :: dict of the acl if it exists
    raises :: NotFoundError if the acl does not exist
    """
    acls = ctx['db']['client']['msample']['core.acl']
    db_entry = acls.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'acl {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return acl_validate(db_entry)
    
def db_update_acl(ctx:dict, data:dict) -> None:
    """
    update a acl in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to update the acl with.

    return :: None
    raises :: NotFoundError if the acl does not exist
    """
    acl_validate(data)
    _id = data.pop('id')
    acls = ctx['db']['client']['msample']['core.acl']
    result = acls.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'acl {id} not found')
    
def db_delete_acl(ctx:dict, id:str) -> None:
    """
    delete a acl from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the acl to delete.

    return :: None
    """
    acls = ctx['db']['client']['msample']['core.acl']
    acls.delete_one({'_id': ObjectId(id)})

def db_list_acl(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list acls from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: list of all acls.
    """
    acls = ctx['db']['client']['msample']['core.acl']
    items = []
    for item in acls.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(acl_validate(item))
    return items

# acl entry #

def db_create_acl_entry(ctx:dict, data:dict) -> dict:
    """
    create a acl entry in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the acl entry with.
    return :: dict of the created acl entry.
    """
    acl_entries = ctx['db']['client']['msample']['core.acl_entry']
    result = acl_entries.insert_one(acl_entry_validate(data))
    data['id'] = str(result.inserted_id)
    return data 

def db_read_acl_entry(ctx:dict, id:str) -> dict:
    """
    read a acl entry from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the acl entry to read.
    
    return :: dict of the acl entry
    raises :: NotFoundError if the acl entry does not exist
    """
    acl_entries = ctx['db']['client']['msample']['core.acl_entry']
    db_entry = acl_entries.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'acl entry {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return acl_entry_validate(db_entry)
    
def db_update_acl_entry(ctx:dict, data:dict) -> None:
    """
    update a acl entry in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to update the acl entry with.

    return :: None
    """
    acl_entry_validate(data)
    _id = data.pop('id')
    acl_entries = ctx['db']['client']['msample']['core.acl_entry']
    result = acl_entries.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'acl entry {id} not found')
    
def db_delete_acl_entry(ctx:dict, id:str) -> None:
    """
    delete a acl entry from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the acl entry to delete.

    return :: None
    """
    acl_entries = ctx['db']['client']['msample']['core.acl_entry']
    acl_entries.delete_one({'_id': ObjectId(id)})

def db_list_acl_entry(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list acl entries from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: list of all acl entries.
    """
    acl_entries = ctx['db']['client']['msample']['core.acl_entry']
    items = []
    for item in acl_entries.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(acl_entry_validate(item))
    return items

