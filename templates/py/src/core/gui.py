import tkinter
from tkinter import ttk

from core.client import create_client_context
# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case", "SampleModule": "module.name.pascal_case"}
from sample_module.gui import SampleModuleIndexPage
# end for ::
# for :: {% for modle in modles.values() %} :: {"sample_module": "modle.module_name.snake_case", "example_item": "model.name.snake_case", "ExampleItem": "model.name.pascal_case"}
from sample_module.example_item.gui import ExampleItemIndexPage, ExampleItemInstancePage
# end for ::

LARGEFONT = ('Verdana', 35)
  
#
#
#

def gui_main(start_frame='MSpecIndexPage'):
    app = MSpecGUIApp(start_frame)
    app.mainloop()
    
class MSpecIndexPage(tkinter.Frame):
     
    def __init__(self, parent, controller:'MSpecGUIApp'): 
        super().__init__(parent)

        label = ttk.Label(self, text='mspec', font=LARGEFONT)
        label.grid(row=0, column=0) 
  
        button1 = ttk.Button(self, text='sample module', command=lambda: controller.show_frame(SampleModuleIndexPage))
        button1.grid(row=1, column=0)


class MSpecGUIApp(tkinter.Tk):

    frame_classes = (
        MSpecIndexPage, 
        SampleModuleIndexPage,
        ExampleItemIndexPage,
        ExampleItemInstancePage
    )

    def __init__(self, start_frame='MSpecIndexPage'):
        super().__init__()
        self.title('mspec')
        self.geometry('1000x800')

        self.ctx = create_client_context()
        
        container = tkinter.Frame(self)
        container.grid(column=0, row=0, sticky='nsew')
  
        self.frames = {}
        self.current_frame = None
  
        for frame_class in self.frame_classes:
            self.frames[frame_class] = frame_class(container, self)
            self.frames[frame_class].grid(row=0, column=0, sticky='nsew')
            self.frames[frame_class].forget()
  
        self.show_frame_str(start_frame)
  
    def show_frame(self, frame_class, **kwargs):
        frame = self.frames[frame_class]
        frame.grid(row=0, column=0, sticky='nsew')
        frame.tkraise()

        try:
            self.current_frame.forget()
        except AttributeError:
            """self.current_frame is None"""

        try:
            frame.on_show_frame(**kwargs)
        except AttributeError:
            pass

        self.current_frame = frame

    def show_frame_str(self, frame_class_str, **kwargs):
        frame_class = globals()[frame_class_str]
        self.show_frame(frame_class, **kwargs)

    def show_index_frame(self, **kwargs):
        self.show_frame(MSpecIndexPage, **kwargs)
