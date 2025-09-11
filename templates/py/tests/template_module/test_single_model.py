import math
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

        # seed data #

        init_response = client_list_single_model(test_ctx, offset=0, limit=101)
        total_items = init_response['total']
        
        if total_items < 15:
            seed_ctx = create_client_context()
            while total_items < 15:
                # insert :: macro.py_test_model_seed_pagination(model)
                item = SingleModel.random()
                client_create_single_model(seed_ctx, item)
                total_items += 1

        test_single_model = SingleModel.example()
        test_single_model.validate()

        # paginate #

        pg_configs = [
            {'page_size': 5, 'expected_pages': math.ceil(total_items / 5)},
            {'page_size': 8, 'expected_pages': math.ceil(total_items / 8)},
            {'page_size': 15, 'expected_pages': math.ceil(total_items / 15)}
        ]

        for pg_config in pg_configs:
            page_size = pg_config['page_size']
            expected_pages = pg_config['expected_pages']

            offset = 0
            item_ids = []
            num_pages = 0
            while True:
                result = client_list_single_model(test_ctx, offset=offset, limit=page_size)
                items = result['items']
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
            self.assertEqual(len(item_ids), total_items)
            self.assertEqual(len(set(item_ids)), total_items)
            

if __name__ == '__main__':
    unittest.main()