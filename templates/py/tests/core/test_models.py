import unittest

from core.exceptions import NotFoundError
from core.models import *
from core.client import *
from core.db import *
from core.types import Meta

from pymongo.collection import Collection

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestModels(unittest.TestCase):

    def test_user_validate(self):

        user_good = user.example()

        user_validated = user_good.validate()
        self.assertEqual(user_good, user_validated)

        user_bad_type = user(
            name='Alice',
            email='alice@nice.com',
            profile=12345
        )
        self.assertRaises(ValueError, user_bad_type.validate)

        user_upper_case = user(
            name='Alice',
            email='Alice@EXAMPLE.com',
            profile='12345'
        )
        user_upper_case.validate()
        self.assertEqual(user_upper_case.email, 'alice@example.com')

    def _disabled_test_user_crud(self):
        """

        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_user = user(
            name='Test User',
            email='test.user@nice.com',
            profile='09876'
        )
        test_user.validate()

        # create #
        created_user = client_create_user(test_ctx, test_user)
        self.assertTrue(isinstance(created_user, user))
        created_user.validate()
        created_user_id = created_user.id
        created_user.id = None
        self.assertEqual(created_user, test_user)

        # read #
        user_read = client_read_user(test_ctx, created_user_id)
        self.assertTrue(isinstance(user_read, user))
        user_read.validate()
        user_read.id = None
        self.assertEqual(user_read, test_user)

        # update #
        user_read.id = created_user_id
        user_read.email = 'test.user.2@nice.com'
        user_read.validate()
        client_update_user(test_ctx, user_read)

        read_after_update = client_read_user(test_ctx, created_user_id)
        self.assertTrue(isinstance(read_after_update, user))
        read_after_update.validate()
        self.assertEqual(read_after_update, user_read)

        # delete #
        client_delete_user(test_ctx, created_user_id)
        self.assertRaises(NotFoundError, client_read_user, test_ctx, created_user_id)

    def _disabled_test_user_list(self):

        collection:Collection = test_ctx['db']['client']['msample']['core.user']
        collection.delete_many({})

        # seed the db #

        sample_user = user.example()

        for _ in range(60):
            client_create_user(test_ctx, sample_user)

        self.assertEqual(collection.count_documents({}), 60)

        # page size 100 #

        for n in range(2):
            items = client_list_users(test_ctx, offset=n*100, limit=100)

            if n == 0:
                self.assertEqual(len(items), 60)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertTrue(isinstance(item, user))
                item.validate()
                item.id = None
                self.assertEqual(item, sample_user)

        # page size 25 #

        for i in range(4):
            items = client_list_users(test_ctx, offset=i*25, limit=25)

            if i < 2:
                self.assertEqual(len(items), 25)
            elif i == 2:
                self.assertEqual(len(items), 10)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertTrue(isinstance(item, user))
                item.validate()
                item.id = None
                self.assertEqual(item, sample_user)

    def test_profile_validate(self):

        profile_good = profile.example()

        profile_validated = profile_good.validate()
        self.assertEqual(profile_good, profile_validated)

        profile_bad_type = profile.example()
        profile_bad_type.bio = 12345
        
        self.assertRaises(ValueError, profile_bad_type.validate)

    def _disabled_test_profile_crud(self):
        test_profile = profile(
            name='Test Profile',
            bio='Test profile bio',
            meta=Meta(
                data={'key': 'value'},
                tags={'tag1', 'tag2'},
                hierarchies={'one/two/three', 'blue/aqua'}
            )
        )

        test_profile.validate()

        # create #
        created_profile = client_create_profile(test_ctx, test_profile)
        self.assertTrue(isinstance(created_profile, profile))
        created_profile.validate()
        created_profile_id = created_profile.id
        created_profile.id = None
        self.assertEqual(created_profile, test_profile)

        # read #
        profile_read = client_read_profile(test_ctx, created_profile_id)
        self.assertTrue(isinstance(profile_read, profile))
        profile_read.validate()
        profile_read.id = None
        self.assertEqual(profile_read, test_profile)

        # update #
        profile_read.id = created_profile_id
        profile_read.name = 'Updated Test Profile'
        profile_read.validate()
        client_update_profile(test_ctx, profile_read)

        read_after_update = client_read_profile(test_ctx, created_profile_id)
        self.assertTrue(isinstance(read_after_update, profile))
        read_after_update.validate()
        self.assertEqual(read_after_update, profile_read)

        # delete #
        client_delete_profile(test_ctx, created_profile_id)
        self.assertRaises(NotFoundError, client_read_profile, test_ctx, created_profile_id)

if __name__ == '__main__':
    unittest.main()
