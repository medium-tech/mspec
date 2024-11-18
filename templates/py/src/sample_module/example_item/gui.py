import tkinter
from tkinter import ttk, StringVar

from sample_module.example_item.client import client_list_example_item

__all__ = [
    'ExampleItemIndexPage',
    'ExampleItemInstancePage'
]

LARGEFONT = ('Verdana', 35)

class ExampleItemIndexPage(tkinter.Frame):
     
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # state #

        self.list_offset = 0
        self.list_page_size = 25
        self.list_items_row_offset = 6
        self.is_first_show = True

        self.list_status = StringVar()
        self.list_status.set('status: initial')

        self.pagination_label = StringVar()
        self.pagination_label.set('-')

        # header #

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item', font=LARGEFONT)
        label.grid(row=0, column=1)

        # contorls #

        self.controls = ttk.Frame(self)
        self.controls.grid(row=4, column=0, columnspan=2, sticky='nsew')

        pagination_label = ttk.Label(self.controls, textvariable=self.pagination_label)
        pagination_label.grid(row=3, column=4, columnspan=2, sticky='w')

        self.prev_pg_button = ttk.Button(self.controls, text='<-', command=lambda: self.prev_pg())
        self.prev_pg_button.state(['disabled'])
        self.prev_pg_button.grid(row=3, column=0)

        load_button = ttk.Button(self.controls, text='load', command=lambda: self._list_fetch())
        load_button.grid(row=3, column=1)

        self.next_pg_button = ttk.Button(self.controls, text='->', command=lambda: self.next_pg())
        self.next_pg_button.grid(row=3, column=2)

        status_label = ttk.Label(self.controls, textvariable=self.list_status)
        status_label.grid(row=2, column=0, columnspan=2, sticky='w')

        # vars :: {"['id', 'description', 'verified', 'color', 'count', 'score', 'tags']": "macro.py_field_list(model.fields)"}
        self.field_names = ['id', 'description', 'verified', 'color', 'count', 'score', 'tags']

        self.table = ttk.Frame(self)
        self.table.grid(row=self.list_items_row_offset, column=0, columnspan=2, sticky='nsew')
        for n, field_name in enumerate(self.field_names):
            header = ttk.Label(self.table, text=field_name)
            header.grid(row=self.list_items_row_offset - 1, column=n)

    def on_show_frame(self):
        if self.is_first_show:
            self.is_first_show = False
            self._list_fetch()
    
    def _list_fetch(self):
        self.list_status.set('status: fetching')
        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} results: -')

        for widget in self.table.winfo_children():
            widget.destroy()

        try:
            example_items = client_list_example_item(self.controller.ctx, offset=self.list_offset, limit=self.list_page_size)
        except Exception as e:
            print(e)
            self.list_status.set('status: error')
            return
        
        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} results: {len(example_items)}')
        
        self.list_status.set('status: ok')
    
        for n in range(self.list_page_size):
            
            try:
                example_item = example_items[n]
            except IndexError:
                example_item = {}

            id_label = ttk.Label(self.table, text=example_item.get('id', '-'))
            id_label.grid(row=n + self.list_items_row_offset, column=0)

            description_label = ttk.Label(self.table, text=example_item.get('description', '-'))
            description_label.grid(row=n + self.list_items_row_offset, column=1)

            verified_label = ttk.Label(self.table, text=str(example_item.get('verified', '-')).lower())
            verified_label.grid(row=n + self.list_items_row_offset, column=2)

            color_label = ttk.Label(self.table, text=example_item.get('color', '-'))
            color_label.grid(row=n + self.list_items_row_offset, column=3)

            count_label = ttk.Label(self.table, text=str(example_item.get('count', '-')))
            count_label.grid(row=n + self.list_items_row_offset, column=4)

            score_label = ttk.Label(self.table, text=str(example_item.get('score', '-')))
            score_label.grid(row=n + self.list_items_row_offset, column=5)

            tags_label = ttk.Label(self.table, text=', '.join(example_item.get('tags', [])))
            tags_label.grid(row=n + self.list_items_row_offset, column=6)

        if self.list_offset == 0:
            self.prev_pg_button.state(['disabled'])
        else:
            self.prev_pg_button.state(['!disabled'])

        if len(example_items) < self.list_page_size:
            self.next_pg_button.state(['disabled'])
        else:
            self.next_pg_button.state(['!disabled'])

    def prev_pg(self):
        self.list_offset = max(0, self.list_offset - self.list_page_size)
        self._list_fetch()

    def next_pg(self):
        self.list_offset += self.list_page_size
        self._list_fetch()


class ExampleItemInstancePage(tkinter.Frame):
     
    def __init__(self, parent, controller): 
        super().__init__(parent)

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item - <id>', font=LARGEFONT)
        label.grid(row=0, column=1) 
