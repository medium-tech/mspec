import unittest
from copy import deepcopy
from msample import verify, to_json, from_json
from msample.client import *
from msample.db import *

example = {
    'name': 'this is a thing',
    'verified': True,
    'color': 'green',
    'age': 42,
    'score': 3.14,
    'tags': ['tag1', 'tag2', 'tag3']
}

new_example = lambda: deepcopy(example)
db_client = db_init()

class TestSampleItem(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        client_init()

    def test_verify(self):
        """
        test the verify function
        """
        verify(example)

        bad_type = new_example()
        bad_type['name'] = 42
        self.assertRaises(TypeError, verify, bad_type)

        bad_key = new_example()
        bad_key['bad_key'] = 'muy mal'
        self.assertRaises(KeyError, verify, bad_key)

    def test_json(self):
        """
        test the json functions
        """
        json_string = to_json(example)
        self.assertIsInstance(json_string, str)

        data = from_json(json_string)
        self.assertIsInstance(data, dict)
        self.assertEqual(data, example)
        verify(data)

    def test_db_crud(self):
        """
~
        only need to test the db, which by proxy tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        # create #
        id = db_create_sample_item(new_example())
        self.assertIsInstance(id, str)
        self.assertGreater(len(id), 0)

        # read #
        item_read = db_read_sample_item(id)
        self.assertIsInstance(item_read, dict)
        verify(item_read)
        del item_read['id']
        self.assertEqual(item_read, example)

        # update #
        item_read['name'] = 'this is a modified thing'
        db_update_sample_item(id, item_read)

        read_after_update = db_read_sample_item(id)
        verify(read_after_update)
        del read_after_update['id']
        self.assertEqual(read_after_update, item_read)
        self.assertNotEqual(read_after_update, example)

        # delete #
        db_delete_sample_item(id)
        item_read_after_delete = db_read_sample_item(id)
        self.assertIsNone(item_read_after_delete)

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
        id = client_create_sample_item(new_example())
        self.assertIsInstance(id, str)
        self.assertGreater(len(id), 0)

        # read #
        item_read = client_read_sample_item(id)
        self.assertIsInstance(item_read, dict)
        verify(item_read)
        self.assertEqual(item_read, example)

        # update #
        item_read['name'] = 'this is a modified thing'
        client_update_sample_item(id, item_read)

        read_after_update = client_read_sample_item(id)
        self.assertEqual(read_after_update, item_read)
        self.assertNotEqual(read_after_update, example)

        # delete #
        client_delete_sample_item(id)
        item_read_after_delete = client_read_sample_item(id)
        self.assertIsNone(item_read_after_delete)

    def test_client_list(self):
        self._test_list(client_list_sample_item)

    def _test_list(self, list_function):

        collection = db_client['sample']['sample_item']

        collection.delete_many({})

        # seed the db #

        for _ in range(60):
            db_create_sample_item(new_example())

        self.assertEqual(collection.count_documents({}), 60)

        # page size 100 #

        for n in range(2):
            items = list_function(offset=n*100, limit=100)

            if n == 0:
                self.assertEqual(len(items), 60)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertIsInstance(item, dict)
                verify(item)
                del item['id']
                self.assertEqual(item, example)

        # page size 25 #

        for i in range(4):
            items = list_function(offset=i*25, limit=25)
            self.assertIsInstance(items, list)

            if i < 2:
                self.assertEqual(len(items), 25)
            elif i == 2:
                self.assertEqual(len(items), 10)
            else:
                self.assertEqual(len(items), 0)

            for item in items:
                self.assertIsInstance(item, dict)
                verify(item)
                del item['id']
                self.assertEqual(item, example)

if __name__ == '__main__':
    unittest.main()
