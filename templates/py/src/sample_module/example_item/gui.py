import tkinter
from tkinter import ttk, StringVar

from sample_module.example_item.client import client_list_example_item

__all__ = [
    'ExampleItemIndexPage',
    'ExampleItemInstancePage'
]

LARGEFONT = ('Verdana', 35)

class ExampleItemIndexPage(tkinter.Frame):
     
    def __init__(self, parent_frame, app:tkinter.Tk):
        super().__init__(parent_frame)
        self.app = app
        self.bind('<Button-1>', lambda _: self.app.focus_set())
        
        # state #

        self.list_offset = 0
        self.list_page_size = 25
        self.list_items_row_offset = 6
        self.is_first_show = True

        self.list_status = StringVar()
        self.list_status.set('status: ')

        self.pagination_label = StringVar()
        self.pagination_label.set('-')

        # header #

        back_button = ttk.Button(self, text='<-', command=lambda: self.app.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item', font=LARGEFONT)
        label.grid(row=0, column=1)
        label.bind('<Button-1>', lambda _: self.app.focus_set())

        # controls #

        self.controls = ttk.Frame(self)
        self.controls.grid(row=4, column=0, columnspan=2, sticky='nsew')
        self.controls.bind('<Button-1>', lambda _: self.app.focus_set())

        pagination_label = ttk.Label(self.controls, textvariable=self.pagination_label)
        pagination_label.grid(row=3, column=4, columnspan=2, sticky='w')

        self.prev_pg_button = ttk.Button(self.controls, text='<-', command=lambda: self.prev_pg(), width=3)
        self.prev_pg_button.state(['disabled'])
        self.prev_pg_button.grid(row=3, column=0)

        load_button = ttk.Button(self.controls, text='load', command=lambda: self._list_fetch(), width=3)
        load_button.grid(row=3, column=1)

        self.next_pg_button = ttk.Button(self.controls, text='->', command=lambda: self.next_pg(), width=3)
        self.next_pg_button.grid(row=3, column=2)

        status_label = ttk.Label(self.controls, textvariable=self.list_status)
        status_label.grid(row=2, column=0, columnspan=2, sticky='w')

        # vars :: {"['id', 'description', 'verified', 'color', 'count', 'score', 'tags']": "macro.py_field_list(model.fields)"}
        self.field_names = ['id', 'description', 'verified', 'color', 'count', 'score', 'tags']

        self.table = ttk.Frame(self)
        self.table.grid(row=self.list_items_row_offset, column=0, columnspan=2, sticky='nsew')

    def on_show_frame(self, **kwargs):
        if self.is_first_show:
            self.is_first_show = False
            self._list_fetch()
    
    def _list_fetch(self):
        self.list_status.set('status: 🟡')
        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} results: -')

        for widget in self.table.winfo_children():
            widget.destroy()

        for n, field_name in enumerate(self.field_names):
            header = ttk.Label(self.table, text=field_name)
            header.grid(row=self.list_items_row_offset - 1, column=n)

        try:
            example_items = client_list_example_item(self.app.ctx, offset=self.list_offset, limit=self.list_page_size)
        except Exception as e:
            print(e)
            self.list_status.set('status: 🔴')
            return
        
        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} results: {len(example_items)}')
        
        self.list_status.set('status: 🟢')

        go_to_item = lambda item: self.app.show_frame_str('ExampleItemInstancePage', item=item)
        padx = 5

        for n in range(self.list_page_size):
            
            try:
                example_item = example_items[n]
            except IndexError:
                example_item = {}

            example_item_id = example_item.get('id', '-')

            if example_item_id == '-':
                go_widget = ttk.Label(self.table, text=example_item_id)
            else:
                go_widget = ttk.Button(self.table, text='go', command=lambda: go_to_item(example_item), width=3)
            go_widget.grid(row=n + self.list_items_row_offset, column=0, padx=padx)

            id_text = tkinter.Text(self.table, height=1, width=25, highlightthickness=0)
            id_text.insert(tkinter.END, example_item_id)
            id_text.grid(row=n + self.list_items_row_offset, column=1, padx=padx)

            description_text = tkinter.Text(self.table, height=1, width=25, highlightthickness=0)
            description_text.insert(tkinter.END, example_item.get('description', '-'))
            description_text.grid(row=n + self.list_items_row_offset, column=2, padx=padx)

            verified_text = tkinter.Text(self.table, height=1, width=6, highlightthickness=0)
            verified_text.insert(tkinter.END, str(example_item.get('verified', '-')).lower())
            verified_text.grid(row=n + self.list_items_row_offset, column=3, padx=padx)

            color_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            color_text.insert(tkinter.END, example_item.get('color', '-'))
            color_text.grid(row=n + self.list_items_row_offset, column=4, padx=padx)

            count_text = tkinter.Text(self.table, height=1, width=7, highlightthickness=0)
            count_text.insert(tkinter.END, str(example_item.get('count', '-')))
            count_text.grid(row=n + self.list_items_row_offset, column=5, padx=padx)

            score_text = tkinter.Text(self.table, height=1, width=7, highlightthickness=0)
            score_text.insert(tkinter.END, str(example_item.get('score', '-')))
            score_text.grid(row=n + self.list_items_row_offset, column=6, padx=padx)

            tags_text = tkinter.Text(self.table, height=1, width=20, highlightthickness=0)
            tags_text.insert(tkinter.END, ', '.join(example_item.get('tags', [])))
            tags_text.grid(row=n + self.list_items_row_offset, column=7, padx=padx)

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
