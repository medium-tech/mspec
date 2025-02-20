import unittest
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
        created_example_item_id = created_example_item.id
        created_example_item.id = None
        self.assertEqual(created_example_item, test_example_item)

        # read #
        example_item_read = client_read_example_item(test_ctx, created_example_item_id)
        self.assertTrue(isinstance(example_item_read, ExampleItem))
        example_item_read.validate()
        example_item_read.id = None
        self.assertEqual(example_item_read, test_example_item)

        # update #
        example_item_read.id = created_example_item_id

        updated_example_item = client_update_example_item(test_ctx, example_item_read)
        self.assertTrue(isinstance(updated_example_item, ExampleItem))
        updated_example_item.validate()
        self.assertEqual(example_item_read, updated_example_item)

        # delete #
        delete_return = client_delete_example_item(test_ctx, created_example_item_id)
        self.assertIsNone(delete_return)
        self.assertRaises(NotFoundError, client_read_example_item, test_ctx, created_example_item_id)

if __name__ == '__main__':
    unittest.main()
