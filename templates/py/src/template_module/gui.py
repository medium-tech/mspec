import tkinter
from tkinter import ttk
from core.types import Fonts
# for :: {% for model in module.models.values() %} :: {"single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}
from template_module.single_model.gui import SingleModelIndexPage
# end for ::
# ignore ::
from template_module.multi_model.gui import MultiModelIndexPage
# end ignore ::

# vars :: {"template_module": "module.name.snake_case", "TemplateModule": "module.name.pascal_case"}

__all__ = [
    'TemplateModuleIndexPage'
]

class TemplateModuleIndexPage(tkinter.Frame):

    index_pages = (
        # for :: {% for model in module.models.values() %} :: {"SingleModel": "model.name.pascal_case", "single model": "model.name.lower_case"}
        (SingleModelIndexPage, 'single model'),
        # end for ::
        # ignore ::
        (MultiModelIndexPage, 'multi model'),
        # end ignore ::
    )

    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.controller = controller
        #self.config(background='white')

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_index_frame())
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='template module', font=Fonts.heading1)
        label.grid(row=0, column=1)

        for n, item in enumerate(self.index_pages, start=1):
            button = ttk.Button(self, text=item[1], command=lambda frame=item[0]: controller.show_frame(frame))
            button.grid(row=n, column=0)
