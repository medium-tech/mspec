# for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
from .sample_item import sample_item_random
from .sample_item.server import sample_item_routes
from .sample_item.db import *
from .sample_item.client import *
# end for ::

# vars :: {"sample": "module.name.snake_case"}

__all__ = [
    'sample_routes',
    'sample_db',
    'sample_client'
]

sample_routes = [
    # for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
    sample_item_routes,
    # end for ::
]

class sample_db:

    @staticmethod
    def seed_data(ctx:dict, count:int=100):
        for _ in range(count):
            # for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
            db_create_sample_item(ctx, sample_item_random())
            # end for ::

    # for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
    create_sample_item = db_create_sample_item
    read_sample_item = db_read_sample_item
    update_sample_item = db_update_sample_item
    delete_sample_item = db_delete_sample_item
    list_sample_item = db_list_sample_item
    # end for ::

class sample_client:
    # for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
    create_sample_item = client_create_sample_item
    read_sample_item = client_read_sample_item
    update_sample_item = client_update_sample_item
    delete_sample_item = client_delete_sample_item
    list_sample_item = client_list_sample_item
    # end for ::