import unittest

from core.exceptions import NotFoundError
from core.models import *
from core.client import *
from core.db import *

from pymongo.collection import Collection

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestExampleItem(unittest.TestCase):

    def test_user_validate(self):

        user_good = {
            'name': 'Alice',
            'email': 'alice@nice.com',
            'profile': '12345'
        }

        user_validated = user_validate(user_good)
        self.assertEqual(user_good, user_validated)

        user_bad_type = {
            'name': 'Alice',
            'email': 'alice@nice.com',
            'profile': 12345
        }
        self.assertRaises(ValueError, user_validate, user_bad_type)

        user_extra_key = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'profile': '12345',
            'extra_key': 'extra_value'
        }
        self.assertRaises(ValueError, user_validate, user_extra_key)

    def test_user_crud(self):
        """

        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_user = {
            'name': 'Test User',
            'email': 'test.user@nice.com',
            'profile': '09876'
        }
        user_validate(test_user)

        # create #
        created_user = client_create_user(test_ctx, test_user)
        user_validate(created_user)
        created_user_id = created_user.pop('id')
        self.assertEqual(created_user, test_user)

        # read #
        user_read = client_read_user(test_ctx, created_user_id)
        user_validate(user_read)
        del user_read['id']
        self.assertEqual(user_read, test_user)

        # update #
        user_read['email'] = 'test.user.2@nice.com'
        user_validate(user_read)
        client_update_user(test_ctx, created_user_id, user_read)

        read_after_update = client_read_user(test_ctx, created_user_id)
        user_validate(read_after_update)

        # delete #
        client_delete_user(test_ctx, created_user_id)
        self.assertRaises(NotFoundError, client_read_user, test_ctx, created_user_id)

    def test_user_list(self):

        collection:Collection = test_ctx['db']['client']['msample']['core.user']
        collection.delete_many({})

        # seed the db #

        user_data = {
            'name': 'Alice',
            'email': 'alice@nice.com',
            'profile': '12345'
        }

        for _ in range(60):
            client_create_user(test_ctx, user_data)

        self.assertEqual(collection.count_documents({}), 60)

        # page size 100 #

        for n in range(2):
            items = client_list_users(test_ctx, offset=n*100, limit=100)

            if n == 0:
                self.assertEqual(len(items), 60)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                user_validate(item)
                del item['id']
                self.assertEqual(item, user_data)

        # page size 25 #

        for i in range(4):
            items = client_list_users(test_ctx, offset=i*25, limit=25)
            self.assertIsInstance(items, list)

            if i < 2:
                self.assertEqual(len(items), 25)
            elif i == 2:
                self.assertEqual(len(items), 10)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                user_validate(item)
                del item['id']
                self.assertEqual(item, user_data)

if __name__ == '__main__':
    unittest.main()
