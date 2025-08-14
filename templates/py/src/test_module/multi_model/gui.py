import tkinter
from copy import deepcopy
from tkinter import ttk, StringVar
from test_module.multi_model.model import MultiModel, field_list, longest_field_name_length
from test_module.multi_model.client import client_list_multi_model

__all__ = [
    'MultiModelIndexPage',
    'MultiModelInstancePage'
]

LARGEFONT = ('Verdana', 35)
TEXT = ('Verdana', 12)

class MultiModelIndexPage(tkinter.Frame):

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

        label = ttk.Label(self, text='multi model', font=LARGEFONT)
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

        # headers
        for n, field_name in enumerate(['', 'id'] + field_list):  # empty str for button column
            header = ttk.Label(self.table, text=field_name)
            header.grid(row=self.list_items_row_offset - 1, column=n)

        try:
            multi_models = client_list_multi_model(self.app.ctx, offset=self.list_offset, limit=self.list_page_size)
        except Exception as e:
            print(e)
            self.list_status.set('status: 🔴')
            return

        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} results: {len(multi_models)}')

        self.list_status.set('status: 🟢')

        padx = 5

        for n in range(self.list_page_size):
            
            try:
                multi_model = multi_models[n]
            except IndexError:
                multi_model = {}

            multi_model_id = getattr(multi_model, 'id', '-')

            if multi_model_id == '-':
                view_widget = ttk.Label(self.table, text=multi_model_id)
            else:
                def go_to_item(item):
                    print(f"Going to item {item.id} in MultiModelInstancePage")
                    self.app.show_frame_str('MultiModelInstancePage', item=item)

                view_widget = ttk.Button(self.table, text='view', command=lambda i=n: go_to_item(multi_models[i]), width=3)

            view_widget.grid(row=n + self.list_items_row_offset, column=0, padx=padx)

            # id - str
            id_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            id_text.insert(tkinter.END, multi_model_id)
            id_text.grid(row=n + self.list_items_row_offset, column=1, padx=padx)

            # macro :: py_tk_multi_bool :: {"multi_bool": "name"}
            # multi_bool - list of bool
            multi_bool_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            multi_bool_value = getattr(multi_model, 'multi_bool', '-')
            if isinstance(multi_bool_value, list):
                multi_bool_value = ', '.join([str(v).lower() for v in multi_bool_value])
            multi_bool_text.insert(tkinter.END, str(multi_bool_value))
            multi_bool_text.grid(row=n + self.list_items_row_offset, column=8, padx=padx)
            # end macro ::

            # macro :: py_tk_multi_int :: {"multi_int": "name"}
            # multi_int - list of int
            multi_int_text = tkinter.Text(self.table, height=1, width=15, highlightthickness=0)
            multi_int_value = getattr(multi_model, 'multi_int', '-')
            if isinstance(multi_int_value, list):
                multi_int_value = ', '.join([str(v) for v in multi_int_value])
            multi_int_text.insert(tkinter.END, str(multi_int_value))
            multi_int_text.grid(row=n + self.list_items_row_offset, column=9, padx=padx)
            # end macro ::

            # macro :: py_tk_multi_float :: {"multi_float": "name"}
            # multi_float - list of float
            multi_float_text = tkinter.Text(self.table, height=1, width=15, highlightthickness=0)
            multi_float_value = getattr(multi_model, 'multi_float', '-')
            if isinstance(multi_float_value, list):
                multi_float_value = ', '.join([str(v) for v in multi_float_value])
            multi_float_text.insert(tkinter.END, str(multi_float_value))
            multi_float_text.grid(row=n + self.list_items_row_offset, column=10, padx=padx)
            # end macro ::

            # macro :: py_tk_multi_string :: {"multi_string": "name"}
            # multi_string - list of str
            multi_string_text = tkinter.Text(self.table, height=1, width=30, highlightthickness=0)
            multi_string_value = getattr(multi_model, 'multi_string', '-')
            if isinstance(multi_string_value, list):
                multi_string_value = ', '.join(multi_string_value)
            multi_string_text.insert(tkinter.END, str(multi_string_value))
            multi_string_text.grid(row=n + self.list_items_row_offset, column=11, padx=padx)
            # end macro ::

            # macro :: py_tk_multi_enum :: {"multi_enum": "name"}
            # multi_enum - list of str (enums)
            multi_enum_text = tkinter.Text(self.table, height=1, width=20, highlightthickness=0)
            multi_enum_value = getattr(multi_model, 'multi_enum', '-')
            if isinstance(multi_enum_value, list):
                multi_enum_value = ','.join(multi_enum_value)
            multi_enum_text.insert(tkinter.END, str(multi_enum_value))
            multi_enum_text.grid(row=n + self.list_items_row_offset, column=12, padx=padx)
            # end macro ::

            # macro :: py_tk_multi_datetime :: {"multi_datetime": "name"}
            # multi_datetime - list of datetime
            multi_datetime_text = tkinter.Text(self.table, height=1, width=30, highlightthickness=0)
            multi_datetime_value = getattr(multi_model, 'multi_datetime', '-')
            if isinstance(multi_datetime_value, list):
                multi_datetime_value = ', '.join([str(v) for v in multi_datetime_value])
            multi_datetime_text.insert(tkinter.END, str(multi_datetime_value))
            multi_datetime_text.grid(row=n + self.list_items_row_offset, column=13, padx=padx)
            # end macro ::

        if self.list_offset == 0:
            self.prev_pg_button.state(['disabled'])
        else:
            self.prev_pg_button.state(['!disabled'])

        if len(multi_models) < self.list_page_size:
            self.next_pg_button.state(['disabled'])
        else:
            self.next_pg_button.state(['!disabled'])

    def prev_pg(self):
        self.list_offset = max(0, self.list_offset - self.list_page_size)
        self._list_fetch()

    def next_pg(self):
        self.list_offset += self.list_page_size
        self._list_fetch()


class MultiModelInstancePage(tkinter.Frame):

    def __init__(self, parent, controller, item=None):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.item:MultiModel = None
        self.item_id = '-'

    def _set_item(self, item):
        self.item = item
        self.item_id = getattr(item, 'id', '-')

    def _draw(self):
        for widget in self.winfo_children():
            widget.destroy()

        back_button = ttk.Button(self, text='<-', command=lambda: self.controller.show_frame_str('MultiModelIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text=f'multi model - {self.item_id}', font=LARGEFONT)
        label.grid(row=0, column=1)

        field_grid = tkinter.Text(self, font=TEXT, wrap='word', height=500, width=100, highlightthickness=0)
        for n, field_name in enumerate(['id'] + field_list):
            field_value = getattr(self.item, field_name, '-')
            if isinstance(field_value, list):
                field_value = ', '.join([str(v) for v in field_value])
            field_display = f'{field_name}:'
            field_grid.insert(tkinter.END, f'{field_display:<{longest_field_name_length + 2}} {field_value}\n\n')
        field_grid.grid(row=1, column=0, columnspan=2)

    def on_show_frame(self, item=None, **kwargs):
        self._set_item(item)
        print(f'Showing MultiModelInstancePage for item: {self.item_id}')
        self._draw()
