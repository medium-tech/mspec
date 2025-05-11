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
            name='Test User auth',
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

        # profile #

        profile = Profile(
            name='Test Profile',
            bio='This is a test profile',
            user_id=created_user.id,
            meta=Meta(
                data={
                    'a': True,
                    'b': 123,
                    'c': 1.23,
                    'd': 'hello.world',
                },
                tags=['tag1', 'tag2'],
                hierarchies=['one/two/three', 'abc/xyz']
            )
        )

        created_profile = client_create_profile(login_ctx, profile)
        self.assertTrue(isinstance(created_profile, Profile))
        created_profile.validate()

        read_profile = client_read_profile(login_ctx, created_profile.id)
        try:
            self.assertEqual(read_profile, created_profile)
        except AssertionError:
            print(created_profile)
            print(read_profile)
            breakpoint()

        # auth errors #

        self.assertRaises(AuthenticationError, client_login, test_ctx, new_user.email, 'wrong-password')
        self.assertRaises(AuthenticationError, client_read_user, test_ctx, created_user.id)
        self.assertRaises(AuthenticationError, client_update_profile, test_ctx, profile)

        other_user_form = CreateUser(
            name='Other Test User auth',
            email=f'other-test-user-auth-{time.time()}@email.com',
            password1='my-test-password',
            password2='my-test-password'
        )
        
        other_user = client_create_user(test_ctx, other_user_form)
        other_login_ctx = client_login(test_ctx, other_user.email, other_user_form.password1)
        self.assertRaises(ForbiddenError, client_read_user, other_login_ctx, created_user.id)
        self.assertRaises(ForbiddenError, client_update_profile, other_login_ctx, profile)

if __name__ == '__main__':
    unittest.main()