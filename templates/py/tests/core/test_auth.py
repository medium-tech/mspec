import unittest

from core.exceptions import *
from core.models import *
from core.client import *
from core.db import *
from core.types import metadata

from pymongo.collection import Collection

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestAuth(unittest.TestCase):

    def test_user_auth(self):
        user_col:Collection = test_ctx['db']['client']['msample']['core.user']
        user_col.delete_many({})

        pw_hash_col:Collection = test_ctx['db']['client']['msample']['core.user_password_hash']
        pw_hash_col.delete_many({})

        # create user #

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

        # login #

        login_ctx = client_login(test_ctx, new_user.email, new_user.password.password1)
        
        read_user = client_read_user(login_ctx, created_user.id)
        self.assertEqual(read_user, created_user)

        # auth errors #

        self.assertRaises(AuthenticationError, client_login, test_ctx, new_user.email, 'wrong-password')
        self.assertRaises(AuthenticationError, client_read_user, test_ctx, created_user.id)

        other_user_form = create_user_form(
            name='Other Test User auth',
            email='other-test-user-auth@email.com',
            password=new_password(
                password1='my-test-password',
                password2='my-test-password'
            )
        )
        
        other_user = client_create_user(test_ctx, other_user_form)
        other_login_ctx = client_login(test_ctx, other_user.email, other_user_form.password.password1)
        self.assertRaises(ForbiddenError, client_read_user, other_login_ctx, created_user.id)

if __name__ == '__main__':
    unittest.main()
