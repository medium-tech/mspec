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
        label = ttk.Label(self, text='example item', font=LARGEFONT)
        label.grid(row=0, column=0, padx=10, pady=10)


class ExampleItemInstancePage(tkinter.Frame):
     
    def __init__(self, parent, controller): 
        super().__init__(parent)

        label = ttk.Label(self, text='example item - <id>', font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10) 
