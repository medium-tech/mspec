import unittest

from core.exceptions import NotFoundError
from core.models import *
from core.client import *
from core.db import *
from core.types import metadata

from pymongo.collection import Collection

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestAuth(unittest.TestCase):

    def test_user_auth(self):
        collection:Collection = test_ctx['db']['client']['msample']['core.user']
        collection.delete_many({})

        new_user = create_user_form(
            name='Test User auth',
            email='test-user-auth@email.com',
            password=new_password(
                password1='my-test-password',
                password2='my-test-password'
            )
        )
        new_user.validate()

        created_user = client_create_user(test_ctx, new_user)
        self.assertTrue(isinstance(created_user, user))
        created_user.validate()
        self.assertTrue(isinstance(created_user.id, str))



if __name__ == '__main__':
    unittest.main()
