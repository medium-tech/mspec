import unittest
import sqlite3

from core.db import create_db_context
from core.client import create_client_context
from core.exceptions import NotFoundError
from template_module.single_model.model import SingleModel
from template_module.single_model.client import *

# vars :: {"template_module": "module.name.snake_case", "single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}

test_ctx = create_db_context()
test_ctx.update(create_client_context())

# insert :: macro.py_test_model_auth_context(model)

class TestSingleModel(unittest.TestCase):

    # insert :: macro.py_test_auth(model)

    def test_single_model_crud(self):
        """
        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_single_model = SingleModel.example()
        test_single_model.validate()

        # create #
        
        created_single_model = client_create_single_model(test_ctx, test_single_model)
        self.assertTrue(isinstance(created_single_model, SingleModel))
        created_single_model.validate()
        test_single_model.id = created_single_model.id

        self.assertEqual(created_single_model, test_single_model)

        # read #

        single_model_read = client_read_single_model(test_ctx, created_single_model.id)
        self.assertTrue(isinstance(single_model_read, SingleModel))
        single_model_read.validate()
        self.assertEqual(single_model_read, test_single_model)
            
        # update #

        updated_single_model = client_update_single_model(test_ctx, single_model_read)
        self.assertTrue(isinstance(updated_single_model, SingleModel))
        updated_single_model.validate()
        self.assertEqual(single_model_read, updated_single_model)

        # delete #

        delete_return = client_delete_single_model(test_ctx, created_single_model.id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_single_model, test_ctx, created_single_model.id)

        cursor:sqlite3.Cursor = test_ctx['db']['cursor']
        fetched_item = cursor.execute(f"SELECT * FROM single_model WHERE id=?", (created_single_model.id,)).fetchone()
        self.assertIsNone(fetched_item)

        # insert :: macro.py_test_crud_delete(model)

    def test_single_model_pagination(self):

        raise Exception('refactor pagination to match multi_model')

        # seed data #

        items = client_list_single_model(test_ctx, offset=0, limit=101)
        items_len = len(items)
        if items_len > 100:
            raise Exception('excpecting 100 items or less, delete db and restart test')
        
        if items_len < 50:
            difference = 50 - items_len
            for _ in range(difference):
                item = SingleModel.random()
                item = client_create_single_model(test_ctx, item)
        elif items_len > 50:
            difference = items_len - 50
            items_to_delete = items[:difference]
            for item in items_to_delete:
                client_delete_single_model(test_ctx, item.id)

        test_single_model = SingleModel.example()
        test_single_model.validate()

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
                items = client_list_single_model(test_ctx, offset=offset, limit=page_size)
                items_len = 0
                for item in items:
                    items_len += 1
                    item.validate()

                    self.assertTrue(isinstance(item, SingleModel))
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