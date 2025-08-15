import tkinter
from tkinter import ttk
# for :: {% for model in module.models.values() %} :: {"single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}
from template_module.single_model.gui import SingleModelIndexPage
# end for ::

# vars :: {"template_module": "module.name.snake_case", "TemplateModule": "module.name.pascal_case"}

__all__ = [
    'TemplateModuleIndexPage'
]

LARGEFONT = ('Verdana', 35)

class TemplateModuleIndexPage(tkinter.Frame):

    index_pages = (
        # for :: {% for model in module.models.values() %} :: {"SingleModel": "model.name.pascal_case", "single model": "model.name.lower_case"}
        (SingleModelIndexPage, 'single model'),
        # end for ::
    )

    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.controller = controller

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_index_frame())
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='template module', font=LARGEFONT)
        label.grid(row=0, column=1) 

        for n, item in enumerate(self.index_pages, start=1):
            button = ttk.Button(self, text=item[1], command=lambda: controller.show_frame(item[0]))
            button.grid(row=n, column=0)