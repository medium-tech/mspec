import tkinter
from tkinter import ttk
# for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case", "ExampleItem": "model.name.pascal_case"}
from .example_item import example_item_random
from .example_item.server import example_item_routes
from .example_item.db import *
from .example_item.client import *
from .example_item.gui import ExampleItemIndexPage
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

LARGEFONT = ('Verdana', 35)

class SampleModuleIndexPage(tkinter.Frame):

    index_pages = (
        # for :: {% for model in module.models.values() %} :: {"ExampleItem": "model.name.pascal_case", "example item": "model.name.lower_case"}
        (ExampleItemIndexPage, 'example item'),
        # end for ::
    )

    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.controller = controller

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_index_frame())
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='sample module', font=LARGEFONT)
        label.grid(row=0, column=1) 

        for n, item in enumerate(self.index_pages, start=1):
            button = ttk.Button(self, text=item[1], command=lambda: controller.show_frame(item[0]))
            button.grid(row=n, column=0)
