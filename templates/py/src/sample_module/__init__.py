from sample_module.example_item.gui import ExampleItemIndexPage
import tkinter
from tkinter import ttk
# for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
from .example_item import example_item_random
from .example_item.server import example_item_routes
from .example_item.db import *
from .example_item.client import *
# end for ::

# vars :: {"sample_module": "module.name.snake_case"}

__all__ = [
    'sample_module_routes',
    'sample_module_db',
    'sample_module_client'
]

sample_module_routes = [
    # for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
    example_item_routes,
    # end for ::
]

class sample_module_db:

    @staticmethod
    def seed_data(ctx:dict, count:int=100):
        for _ in range(count):
            # for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
            db_create_example_item(ctx, example_item_random())
            # end for ::

    # for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
    create_example_item = db_create_example_item
    read_example_item = db_read_example_item
    update_example_item = db_update_example_item
    delete_example_item = db_delete_example_item
    list_example_item = db_list_example_item
    # end for ::

class sample_module_client:
    # for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
    create_example_item = client_create_example_item
    read_example_item = client_read_example_item
    update_example_item = client_update_example_item
    delete_example_item = client_delete_example_item
    list_example_item = client_list_example_item
    # end for ::

LARGEFONT = ('Verdana', 35)

class SampleModuleIndexPage(tkinter.Frame):

    def __init__(self, parent, controller): 
        super().__init__(parent)

        label = ttk.Label(self, text='sample module', font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10) 
  
        button1 = ttk.Button(self, text='example item', command=lambda: controller.show_frame(ExampleItemIndexPage))
        button1.grid(row=1, column=1, padx=10, pady=10)
