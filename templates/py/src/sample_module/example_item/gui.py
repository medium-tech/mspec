import tkinter
from tkinter import ttk

__all__ = [
    'ExampleItemIndexPage',
    'ExampleItemInstancePage'
]

LARGEFONT = ('Verdana', 35)

class ExampleItemIndexPage(tkinter.Frame):
     
    def __init__(self, parent, controller):
        super().__init__(parent)
        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item', font=LARGEFONT)
        label.grid(row=0, column=1)


class ExampleItemInstancePage(tkinter.Frame):
     
    def __init__(self, parent, controller): 
        super().__init__(parent)

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item - <id>', font=LARGEFONT)
        label.grid(row=0, column=1) 
