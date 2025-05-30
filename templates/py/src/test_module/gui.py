import tkinter
from tkinter import ttk
# for :: {% for model in module.models.values() %} :: {"test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case"}
from test_module.test_model.gui import TestModelIndexPage
# end for ::

# vars :: {"test_module": "module.name.snake_case", "TestModule": "module.name.pascal_case"}

__all__ = [
    'TestModuleIndexPage'
]

LARGEFONT = ('Verdana', 35)

class TestModuleIndexPage(tkinter.Frame):

    index_pages = (
        # for :: {% for model in module.models.values() %} :: {"TestModel": "model.name.pascal_case", "test model": "model.name.lower_case"}
        (TestModelIndexPage, 'test model'),
        # end for ::
    )

    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.controller = controller

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_index_frame())
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='test module', font=LARGEFONT)
        label.grid(row=0, column=1) 

        for n, item in enumerate(self.index_pages, start=1):
            button = ttk.Button(self, text=item[1], command=lambda: controller.show_frame(item[0]))
            button.grid(row=n, column=0)