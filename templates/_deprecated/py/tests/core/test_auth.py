import unittest
import time

from core.types import Meta
from core.exceptions import *
from core.models import *
from core.client import *
from core.db import *

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestAuth(unittest.TestCase):

    def test_user_auth(self):

        # create user #

        new_user = CreateUser(
            name='Test User Auth',
            email=f'test-user-auth-{time.time()}@email.com',
            password1='my-test-password',
            password2='my-test-password',
        )
        new_user.validate()

        created_user = client_create_user(test_ctx, new_user)
        self.assertTrue(isinstance(created_user, User))
        created_user.validate()
        self.assertTrue(isinstance(created_user.id, str))

        # login #

        login_ctx = client_login(test_ctx, new_user.email, new_user.password1)
        
        read_user = client_read_user(login_ctx, created_user.id)
        self.assertEqual(read_user, created_user)

        # auth errors #

        self.assertRaises(AuthenticationError, client_login, test_ctx, new_user.email, 'wrong-password')
        self.assertRaises(AuthenticationError, client_read_user, test_ctx, created_user.id)

        other_user_form = CreateUser(
            name='Other Test User auth',
            email=f'other-test-user-auth-{time.time()}@email.com',
            password1='my-test-password',
            password2='my-test-password'
        )
        
        other_user = client_create_user(test_ctx, other_user_form)
        other_login_ctx = client_login(test_ctx, other_user.email, other_user_form.password1)
        self.assertRaises(ForbiddenError, client_read_user, other_login_ctx, created_user.id)

if __name__ == '__main__':
    unittest.main()