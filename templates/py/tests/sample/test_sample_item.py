import unittest
from core.db import create_db_context
from core.client import create_client_context
from core.exceptions import NotFoundError
from sample.sample_item import sample_item_verify, sample_item_to_json, sample_item_from_json, sample_item_example
from sample.sample_item.client import *
from sample.sample_item.db import db_create_sample_item, db_read_sample_item, db_update_sample_item, db_delete_sample_item, db_list_sample_item

# vars :: {"sample": "module.name.snake_case", "sample_item": "model.name.snake_case", "SampleItem": "model.name.pascal_case", "msample": "project.name.snake_case"}

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestSampleItem(unittest.TestCase):

    def test_verify(self):
        """
        test the verify function
        """
        sample_item_verify(sample_item_example())

        bad_key = sample_item_example()
        bad_key['bad_key'] = 'muy mal'
        self.assertRaises(KeyError, sample_item_verify, bad_key)

    def test_json(self):
        """
        test the json functions
        """
        json_string = sample_item_to_json(sample_item_example())
        self.assertIsInstance(json_string, str)

        data = sample_item_from_json(json_string)
        self.assertIsInstance(data, dict)
        self.assertEqual(data, sample_item_example())
        sample_item_verify(data)

    def test_db_crud(self):
        """
        only need to test the db, which by proxy tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        # create #
        id = db_create_sample_item(test_ctx, sample_item_example())
        self.assertIsInstance(id, str)
        self.assertGreater(len(id), 0)

        # read #
        item_read = db_read_sample_item(test_ctx, id)
        self.assertIsInstance(item_read, dict)
        sample_item_verify(item_read)
        del item_read['id']
        self.assertEqual(item_read, sample_item_example())

        # update #
        db_update_sample_item(test_ctx, id, item_read)

        read_after_update = db_read_sample_item(test_ctx, id)
        sample_item_verify(read_after_update)

        # delete #
        db_delete_sample_item(test_ctx, id)
        self.assertRaises(NotFoundError, db_read_sample_item, test_ctx, id)

    def test_db_list(self):
        self._test_list(db_list_sample_item)

    def test_client_crud(self):
        """

        only need to test the client, which by proxy tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        # create #
        id = client_create_sample_item(test_ctx, sample_item_example())
        self.assertIsInstance(id, str)
        self.assertGreater(len(id), 0)

        # read #
        item_read = client_read_sample_item(test_ctx, id)
        self.assertIsInstance(item_read, dict)
        sample_item_verify(item_read)
        del item_read['id']
        self.assertEqual(item_read, sample_item_example())

        # update #
        client_update_sample_item(test_ctx, id, item_read)
        read_after_update = client_read_sample_item(test_ctx, id)
        sample_item_verify(read_after_update)

        # delete #
        client_delete_sample_item(test_ctx, id)
        self.assertRaises(Exception, client_read_sample_item, test_ctx, id)

    def test_client_list(self):
        self._test_list(client_list_sample_item)

    def _test_list(self, list_function):

        collection = test_ctx['db']['client']['msample']['sample.sample_item']
        collection.delete_many({})

        # seed the db #

        for _ in range(60):
            db_create_sample_item(test_ctx, sample_item_example())

        self.assertEqual(collection.count_documents({}), 60)

        # page size 100 #

        for n in range(2):
            items = list_function(test_ctx, offset=n*100, limit=100)

            if n == 0:
                self.assertEqual(len(items), 60)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertIsInstance(item, dict)
                sample_item_verify(item)
                del item['id']
                self.assertEqual(item, sample_item_example())

        # page size 25 #

        for i in range(4):
            items = list_function(test_ctx, offset=i*25, limit=25)
            self.assertIsInstance(items, list)

            if i < 2:
                self.assertEqual(len(items), 25)
            elif i == 2:
                self.assertEqual(len(items), 10)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertIsInstance(item, dict)
                sample_item_verify(item)
                del item['id']
                self.assertEqual(item, sample_item_example())

if __name__ == '__main__':
    unittest.main()
