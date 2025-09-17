import unittest
import sqlite3
import time
import math

from core.db import create_db_context
from core.client import *
from core.models import *
from core.exceptions import *
from template_module.multi_model.model import MultiModel
from template_module.multi_model.client import *

# vars :: {"template_module": "module.name.snake_case", "multi_model": "model.name.snake_case", "MultiModel": "model.name.pascal_case"}

def test_ctx_init() -> dict:
    ctx = create_db_context()
    ctx.update(create_client_context())
    return ctx

# macro :: py_test_model_auth_context_new_user :: {"multi-model": "model_name_kebab_case", "MultiModel": "model_name_pascal_case"}
# create user for auth testing
def new_user() -> tuple[dict, User]:
    new_ctx = test_ctx_init()
    user = CreateUser(
        name='Test MultiModel Auth',
        email=f'test-multi-model-auth-{time.time()}@email.com',
        password1='my-test-password',
        password2='my-test-password',
    )
    created_user = client_create_user(new_ctx, user)
    login_ctx = client_login(new_ctx, created_user.email, user.password1)
    return login_ctx, created_user
# end macro ::


class TestMultiModel(unittest.TestCase):

    # macro :: py_test_auth_require_login :: {"multi_model": "model_name_snake_case", "MultiModel": "model_name_pascal_case"}
    def test_multi_model_auth(self):
        test_multi_model = MultiModel.example()
        test_multi_model.validate()

        logged_out_ctx = test_ctx_init()

        # should not be able to create multi_model if logged out #
        self.assertRaises(AuthenticationError, client_create_multi_model, logged_out_ctx, test_multi_model)
    # end macro ::

    # macro :: py_test_auth_max_models :: {"multi_model": "model_name_snake_case", "MultiModel": "model_name_pascal_case", "1": "max_models_per_user"}
    def test_multi_model_auth_max_models(self):

        max_models_ctx, _user = new_user()

        for _ in range(1):
            client_create_multi_model(max_models_ctx, MultiModel.example())

        self.assertRaises(Exception, client_create_multi_model, max_models_ctx, MultiModel.example())
    # end macro ::


    def test_multi_model_crud(self):
        """
        only need to test the client, which by also tests the server and other modules

        + create
        + read
        + update
        + delete
        """

        crud_ctx = test_ctx_init()
        # macro :: py_test_model_crud_context_new_user :: {}
        new_user_ctx, _user = new_user()
        crud_ctx.update(new_user_ctx)
        # end macro ::

        test_multi_model = MultiModel.example()
        try:
            test_multi_model.user_id = ''
        except AttributeError:
            """ignore if model does not have user_id"""
        test_multi_model.validate()

        # create #

        created_multi_model = client_create_multi_model(crud_ctx, test_multi_model)
        self.assertTrue(isinstance(created_multi_model, MultiModel))
        created_multi_model.validate()
        test_multi_model.id = created_multi_model.id
        try:
            test_multi_model.user_id = created_multi_model.user_id
        except AttributeError:
            pass

        self.assertEqual(created_multi_model, test_multi_model)

        # read #

        test_multi_model_read = client_read_multi_model(crud_ctx, created_multi_model.id)
        self.assertTrue(isinstance(test_multi_model_read, MultiModel))
        test_multi_model_read.validate()
        self.assertEqual(test_multi_model_read, test_multi_model)

        # update #

        updated_test_multi_model = client_update_multi_model(crud_ctx, test_multi_model_read)
        self.assertTrue(isinstance(updated_test_multi_model, MultiModel))
        updated_test_multi_model.validate()
        self.assertEqual(test_multi_model_read, updated_test_multi_model)

        # delete #

        delete_return = client_delete_multi_model(crud_ctx, created_multi_model.id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_multi_model, crud_ctx, created_multi_model.id)

        cursor:sqlite3.Cursor = crud_ctx['db']['cursor']
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

        pagination_ctx = test_ctx_init()

        # seed data #

        init_response = client_list_multi_model(pagination_ctx, offset=0, limit=1)
        total_items = init_response['total']
        
        if total_items < 15:
            seed_ctx = create_client_context()
            while total_items < 15:
                # macro :: py_test_model_seed_pagination_new_user :: {"1": "max_models_per_user"}
                # create new user(s) to avoid max models per user limits
                if total_items % 1 == 0:
                    new_user_ctx, _user = new_user()
                    seed_ctx.update(new_user_ctx)
                # end macro ::

                item = MultiModel.random()
                client_create_multi_model(seed_ctx, item)
                total_items += 1

        # paginate #

        pg_configs = [
            {'page_size': 5, 'expected_pages': math.ceil(total_items / 5)},
            {'page_size': 8, 'expected_pages': math.ceil(total_items / 8)},
            {'page_size': 15, 'expected_pages': math.ceil(total_items / 15)},
        ]

        for pg_config in pg_configs:
            page_size = pg_config['page_size']
            expected_pages = pg_config['expected_pages']

            offset = 0
            item_ids = []
            num_pages = 0
            while True:
                response = client_list_multi_model(pagination_ctx, offset=offset, limit=page_size)
                returned_items = 0
                for item in response['items']:
                    returned_items += 1
                    item.validate()

                    self.assertTrue(isinstance(item, MultiModel))
                    item_ids.append(item.id)

                if returned_items > 0:
                    num_pages += 1

                if returned_items < page_size:
                    break

                self.assertTrue(returned_items <= page_size)

                offset += page_size
                
            self.assertEqual(num_pages, expected_pages)
            self.assertEqual(len(item_ids), total_items)
            self.assertEqual(len(set(item_ids)), total_items)


if __name__ == '__main__':
    unittest.main()