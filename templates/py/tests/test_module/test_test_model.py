import unittest
import sqlite3

from core.db import create_db_context
from core.client import create_client_context
from core.exceptions import NotFoundError
from test_module.test_model.model import TestModel
from test_module.test_model.client import *

# vars :: {"test_module": "module.name.snake_case", "test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case"}

test_ctx = create_db_context()
test_ctx.update(create_client_context())

class TestTestModel(unittest.TestCase):

    def test_test_model_crud(self):
        """
        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_test_model = TestModel.example()
        test_test_model.validate()

        # create #
        
        created_test_model = client_create_test_model(test_ctx, test_test_model)
        self.assertTrue(isinstance(created_test_model, TestModel))
        created_test_model.validate()
        test_test_model.id = created_test_model.id

        self.assertEqual(created_test_model, test_test_model)

        # read #

        test_model_read = client_read_test_model(test_ctx, created_test_model.id)
        self.assertTrue(isinstance(test_model_read, TestModel))
        test_model_read.validate()
        self.assertEqual(test_model_read, test_test_model)
            
        # update #

        updated_test_model = client_update_test_model(test_ctx, test_model_read)
        self.assertTrue(isinstance(updated_test_model, TestModel))
        updated_test_model.validate()
        self.assertEqual(test_model_read, updated_test_model)

        # delete #

        delete_return = client_delete_test_model(test_ctx, created_test_model.id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_test_model, test_ctx, created_test_model.id)

        cursor:sqlite3.Cursor = test_ctx['db']['cursor']
        fetched_item = cursor.execute(f"SELECT * FROM test_model WHERE id=?", (created_test_model.id,)).fetchone()
        self.assertIsNone(fetched_item)

        # insert :: macro.py_test_crud_delete(model)
        # macro :: py_test_sql_delete :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
        multi_bool_result = cursor.execute(f"SELECT value FROM test_model_multi_bool WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_bool_result.fetchall()), 0)
        # end macro ::

        # ignore ::
        multi_int_result = cursor.execute(f"SELECT value FROM test_model_multi_int WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_int_result.fetchall()), 0)

        multi_float_result = cursor.execute(f"SELECT value FROM test_model_multi_float WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_float_result.fetchall()), 0)

        multi_string_result = cursor.execute(f"SELECT value FROM test_model_multi_string WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_string_result.fetchall()), 0)

        multi_enum_result = cursor.execute(f"SELECT value FROM test_model_multi_enum WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_enum_result.fetchall()), 0)

        multi_datetime_result = cursor.execute(f"SELECT value FROM test_model_multi_datetime WHERE test_model_id=? ORDER BY position", (created_test_model.id,))
        self.assertEqual(len(multi_datetime_result.fetchall()), 0)
        # end ignore ::
        

    def test_test_model_pagination(self):

        # seed data #

        items = client_list_test_model(test_ctx, offset=0, limit=101)
        items_len = len(items)
        if items_len > 100:
            raise Exception('excpecting 100 items or less, delete db and restart test')
        
        if items_len < 50:
            difference = 50 - items_len
            for _ in range(difference):
                item = TestModel.random()
                item = client_create_test_model(test_ctx, item)
        elif items_len > 50:
            difference = items_len - 50
            items_to_delete = items[:difference]
            for item in items_to_delete:
                client_delete_test_model(test_ctx, item.id)

        test_test_model = TestModel.example()
        test_test_model.validate()

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
                items = client_list_test_model(test_ctx, offset=offset, limit=page_size)
                items_len = 0
                for item in items:
                    items_len += 1
                    item.validate()

                    self.assertTrue(isinstance(item, TestModel))
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