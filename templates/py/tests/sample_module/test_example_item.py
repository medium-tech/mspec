import unittest
import sqlite3

from core.db import create_db_context
from core.client import create_client_context
from core.exceptions import NotFoundError
from sample_module.example_item.model import ExampleItem
from sample_module.example_item.client import *

# vars :: {"sample_module": "module.name.snake_case", "example_item": "model.name.snake_case", "ExampleItem": "model.name.pascal_case", "msample": "project.name.snake_case"}

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestExampleItem(unittest.TestCase):

    def test_example_item_crud(self):
        """
        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_example_item = ExampleItem.example()
        test_example_item.validate()

        # create #
        
        created_example_item = client_create_example_item(test_ctx, test_example_item)
        self.assertTrue(isinstance(created_example_item, ExampleItem))
        created_example_item.validate()
        test_example_item.id = created_example_item.id

        self.assertEqual(created_example_item, test_example_item)

        # read #

        example_item_read = client_read_example_item(test_ctx, created_example_item.id)
        self.assertTrue(isinstance(example_item_read, ExampleItem))
        example_item_read.validate()
        self.assertEqual(example_item_read, test_example_item)
            
        # update #

        updated_example_item = client_update_example_item(test_ctx, example_item_read)
        self.assertTrue(isinstance(updated_example_item, ExampleItem))
        updated_example_item.validate()
        self.assertEqual(example_item_read, updated_example_item)

        # delete #

        delete_return = client_delete_example_item(test_ctx, created_example_item.id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_example_item, test_ctx, created_example_item.id)

        cursor:sqlite3.Cursor = test_ctx['db']['cursor']
        fetched_item = cursor.execute(f"SELECT * FROM example_item WHERE id=?", (created_example_item.id,)).fetchone()
        self.assertIsNone(fetched_item)

        # insert :: macro.py_test_crud_delete(model)
        # macro :: py_test_sql_delete :: {"example_item": "model_name_snake_case", "stuff": "field_name"}
        stuff_result = cursor.execute(f"SELECT value FROM example_item_stuff WHERE example_item_id=? ORDER BY position", (created_example_item.id,))
        self.assertEqual(len(stuff_result.fetchall()), 0)
        # end macro ::

    def test_example_item_pagination(self):

        # seed data #

        items = client_list_example_item(test_ctx, offset=0, limit=51)
        items_len = len(items)
        if items_len > 50:
            raise Exception('excpecting 50 items or less, delete db and restart test')
        elif items_len < 50:
            difference = 50 - items_len
            for _ in range(difference):
                item = ExampleItem.random()
                item = client_create_example_item(test_ctx, item)

        test_example_item = ExampleItem.example()
        test_example_item.validate()

        # paginate #

        pg_configs = [
            {'page_size': 10, 'expected_pages': 5},
            {'page_size': 20, 'expected_pages': 3},
            {'page_size': 25, 'expected_pages': 2},
            {'page_size': 50, 'expected_pages': 1}
        ]

        for pg_config in pg_configs:
            page_size = pg_config['page_size']
            expected_pages = pg_config['expected_pages']

            offset = 0
            item_ids = []
            num_pages = 0
            while True:
                items = client_list_example_item(test_ctx, offset=offset, limit=page_size)
                items_len = 0
                for item in items:
                    items_len += 1
                    item.validate()

                    self.assertTrue(isinstance(item, ExampleItem))
                    item_ids.append(item.id)

                if items_len > 0:
                    num_pages += 1

                if items_len < page_size:
                    break

                self.assertTrue(items_len <= page_size)

                offset += page_size
                
            self.assertEqual(num_pages, expected_pages)
            self.assertEqual(len(item_ids), 50)
            self.assertEqual(len(set(item_ids)), 50)
            

if __name__ == '__main__':
    unittest.main()
