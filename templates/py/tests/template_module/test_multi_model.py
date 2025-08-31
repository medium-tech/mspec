import unittest
import sqlite3
import time

from core.db import create_db_context
from core.client import *
from core.models import User, CreateUser
from core.exceptions import AuthenticationError, NotFoundError
from template_module.multi_model.model import MultiModel
from template_module.multi_model.client import *

# vars :: {"template_module": "module.name.snake_case", "multi_model": "model.name.snake_case", "MultiModel": "model.name.pascal_case"}

test_ctx = create_db_context()
test_ctx.update(create_client_context())

# macro :: py_test_model_auth_context :: {"multi-model": "model.name.kebab_case", "MultiModel": "model.name.pascal_case"}
# create user for auth testing
new_user = CreateUser(
    name='Test MultiModel Auth',
    email=f'test-multi-model-auth-{time.time()}@email.com',
    password1='my-test-password',
    password2='my-test-password',
)

created_user = client_create_user(test_ctx, new_user)
login_ctx = client_login(test_ctx, new_user.email, new_user.password1)
test_ctx.update(login_ctx)
# end macro ::


class TestMultiModel(unittest.TestCase):

    # macro :: py_test_auth :: {"multi_model": "model_name_snake_case"}
    def test_multi_model_auth(self):
        test_multi_model = MultiModel.example()
        test_multi_model.validate()

        # should not be able to create multi_model if logged out #
        logged_out_ctx = create_db_context()
        logged_out_ctx.update(create_client_context())
        self.assertRaises(AuthenticationError, client_create_multi_model, logged_out_ctx, test_multi_model)
    # end macro ::

    def test_multi_model_crud(self):
        """
        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        test_multi_model = MultiModel.example()
        test_multi_model.validate()

        # create #

        created_multi_model = client_create_multi_model(test_ctx, test_multi_model)
        self.assertTrue(isinstance(created_multi_model, MultiModel))
        created_multi_model.validate()
        test_multi_model.id = created_multi_model.id

        self.assertEqual(created_multi_model, test_multi_model)

        # read #

        test_multi_model_read = client_read_multi_model(test_ctx, created_multi_model.id)
        self.assertTrue(isinstance(test_multi_model_read, MultiModel))
        test_multi_model_read.validate()
        self.assertEqual(test_multi_model_read, test_multi_model)

        # update #

        updated_test_multi_model = client_update_multi_model(test_ctx, test_multi_model_read)
        self.assertTrue(isinstance(updated_test_multi_model, MultiModel))
        updated_test_multi_model.validate()
        self.assertEqual(test_multi_model_read, updated_test_multi_model)

        # delete #

        delete_return = client_delete_multi_model(test_ctx, created_multi_model.id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_multi_model, test_ctx, created_multi_model.id)

        cursor:sqlite3.Cursor = test_ctx['db']['cursor']
        fetched_item = cursor.execute(f"SELECT * FROM multi_model WHERE id=?", (created_multi_model.id,)).fetchone()
        self.assertIsNone(fetched_item)

        # macro :: py_test_sql_delete :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
        multi_bool_result = cursor.execute(f"SELECT value FROM multi_model_multi_bool WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_bool_result.fetchall()), 0)
        # end macro ::

        multi_int_result = cursor.execute(f"SELECT value FROM multi_model_multi_int WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_int_result.fetchall()), 0)

        multi_float_result = cursor.execute(f"SELECT value FROM multi_model_multi_float WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_float_result.fetchall()), 0)

        multi_string_result = cursor.execute(f"SELECT value FROM multi_model_multi_string WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_string_result.fetchall()), 0)

        multi_enum_result = cursor.execute(f"SELECT value FROM multi_model_multi_enum WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_enum_result.fetchall()), 0)

        multi_datetime_result = cursor.execute(f"SELECT value FROM multi_model_multi_datetime WHERE multi_model_id=? ORDER BY position", (created_multi_model.id,))
        self.assertEqual(len(multi_datetime_result.fetchall()), 0)
        

    def test_multi_model_pagination(self):

        # seed data #

        items = client_list_multi_model(test_ctx, offset=0, limit=101)
        items_len = len(items)
        if items_len > 100:
            raise Exception('excpecting 100 items or less, delete db and restart test')
        
        if items_len < 50:
            difference = 50 - items_len
            for _ in range(difference):
                item = MultiModel.random()
                item = client_create_multi_model(test_ctx, item)
        elif items_len > 50:
            difference = items_len - 50
            items_to_delete = items[:difference]
            for item in items_to_delete:
                client_delete_multi_model(test_ctx, item.id)

        test_multi_model = MultiModel.example()
        test_multi_model.validate()

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
                items = client_list_multi_model(test_ctx, offset=offset, limit=page_size)
                items_len = 0
                for item in items:
                    items_len += 1
                    item.validate()

                    self.assertTrue(isinstance(item, MultiModel))
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