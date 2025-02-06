#!/usr/bin/env python3
from typing import *


class ContentId(str):
    def __init__(self, value):
        super().__init__()

class ACL(object):
    def __init__(self, name:str, admin:str):
        self.name = name
        self.admin = admin
    
    def validate(self):
        if not isinstance(self.name, str):
            raise ValueError('name must be a string')
        if not isinstance(self.admin, str):
            raise ValueError('admin must be a string')


test_id = ContentId('12345')
print(f'{type(test_id)}: {test_id}')

assert isinstance(test_id, ContentId)
assert isinstance(test_id, str)
assert test_id == '12345'

test_acl = ACL('test_acl', 'admin_user')
print(f'{type(test_acl)}: {test_acl}, {test_acl.name}, {test_acl.admin}')

test_acl.validate()
assert isinstance(test_acl, ACL)
assert isinstance(test_acl, object)
assert isinstance(test_acl.name, str)
assert isinstance(test_acl.admin, str)
