import tkinter
from tkinter import ttk, StringVar
from core.types import Fonts
from template_module.single_model.model import SingleModel, field_list, longest_field_name_length
from template_module.single_model.client import client_list_single_model

# vars :: {"template_module": "module.name.snake_case", "TemplateModule": "module.name.pascal_case"}
# vars :: {"SingleModel": "model.name.pascal_case", "single_model": "model.name.snake_case", "single model": "model.name.lower_case"}

__all__ = [
    'SingleModelIndexPage',
    'SingleModelInstancePage'
]

class SingleModelIndexPage(tkinter.Frame):
     
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

        back_button = ttk.Button(self, text='<-', command=lambda: self.app.show_frame_str('TemplateModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='single model', font=Fonts.heading1)
        label.grid(row=0, column=1)
        label.bind('<Button-1>', lambda _: self.app.focus_set())

        # controls #

        self.controls = ttk.Frame(self, style='TFrame')
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

        self.table = ttk.Frame(self, style='TFrame')
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
        
        self.update()
        self.update_idletasks()

        # headers
        for n, field_name in enumerate(['', 'id'] + field_list):  # empty str for button column
            header = ttk.Label(self.table, text=field_name)
            header.grid(row=self.list_items_row_offset - 1, column=n)

        try:
            list_response = client_list_single_model(self.app.ctx, offset=self.list_offset, limit=self.list_page_size)
        except Exception as e:
            print(e)
            self.list_status.set('status: 🔴')
            return
        
        items = list_response['items']
        
        self.pagination_label.set(f'offset: {self.list_offset} limit: {self.list_page_size} count: {len(items)} total: {list_response["total"]}')
        
        self.list_status.set('status: 🟢')

        padx = 5

        for n in range(self.list_page_size):
            
            try:
                item = items[n]
            except IndexError:
                break

            item_id = getattr(item, 'id', '-')

            if item_id == '-':
                view_widget = ttk.Label(self.table, text=item_id)
            else:
                def go_to_item(_item):
                    print(f"Going to item {_item.id} in SingleModelInstancePage")
                    self.app.show_frame_str('SingleModelInstancePage', item=_item)

                view_widget = ttk.Button(self.table, text='view', command=lambda i=n: go_to_item(items[i]), width=3)

            view_widget.grid(row=n + self.list_items_row_offset, column=0, padx=padx)

            # id - str
            id_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            id_text.insert(tkinter.END, item_id)
            id_text.grid(row=n + self.list_items_row_offset, column=1, padx=padx)

            # macro :: py_tk_field_table_bool :: {"single_bool": "field.name.snake_case", "2": "column"}
            # single_bool - bool
            single_bool_text = tkinter.Text(self.table, height=1, width=5, highlightthickness=0)
            single_bool_text.insert(tkinter.END, str(getattr(item, 'single_bool', '-')).lower())
            single_bool_text.grid(row=n + self.list_items_row_offset, column=2, padx=padx)
            # end macro ::

            # macro :: py_tk_field_table_int :: {"single_int": "field.name.snake_case", "3": "column"}
            # single_int - int
            single_int_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            single_int_text.insert(tkinter.END, str(getattr(item, 'single_int', '-')))
            single_int_text.grid(row=n + self.list_items_row_offset, column=3, padx=padx)
            # end macro ::

            # macro :: py_tk_field_table_float :: {"single_float": "field.name.snake_case", "4": "column"}
            # single_float - float
            single_float_text = tkinter.Text(self.table, height=1, width=10, highlightthickness=0)
            single_float_text.insert(tkinter.END, str(getattr(item, 'single_float', '-')))
            single_float_text.grid(row=n + self.list_items_row_offset, column=4, padx=padx)
            # end macro ::

            # macro :: py_tk_field_table_str :: {"single_string": "field.name.snake_case", "5": "column"}
            # single_string - str
            single_string_text = tkinter.Text(self.table, height=1, width=20, highlightthickness=0)
            single_string_text.insert(tkinter.END, getattr(item, 'single_string', '-'))
            single_string_text.grid(row=n + self.list_items_row_offset, column=5, padx=padx)
            # end macro ::

            # macro :: py_tk_field_table_str_enum :: {"single_enum": "field.name.snake_case", "6": "column"}
            # single_enum - str
            single_enum_text = tkinter.Text(self.table, height=1, width=15, highlightthickness=0)
            single_enum_text.insert(tkinter.END, getattr(item, 'single_enum', '-'))
            single_enum_text.grid(row=n + self.list_items_row_offset, column=6, padx=padx)
            # end macro ::

            # macro :: py_tk_field_table_datetime :: {"single_datetime": "field.name.snake_case", "7": "column"}
            # single_datetime - datetime
            single_datetime_text = tkinter.Text(self.table, height=1, width=20, highlightthickness=0)
            single_datetime_value = getattr(item, 'single_datetime', '-')
            if single_datetime_value != '-':
                single_datetime_value = single_datetime_value.strftime('%Y-%m-%d %H:%M:%S')
            single_datetime_text.insert(tkinter.END, str(single_datetime_value))
            single_datetime_text.grid(row=n + self.list_items_row_offset, column=7, padx=padx)
            # end macro ::

            # for :: {% for index, field in enumerate(model.sorted_fields, start=2) %} :: {}
                # insert :: macro_by_type('py_tk_field_table', field.type_id, field=field, column=index)
            # end for ::

        if self.list_offset == 0:
            self.prev_pg_button.state(['disabled'])
        else:
            self.prev_pg_button.state(['!disabled'])

        if len(items) < self.list_page_size:
            self.next_pg_button.state(['disabled'])
        else:
            self.next_pg_button.state(['!disabled'])

    def prev_pg(self):
        self.list_offset = max(0, self.list_offset - self.list_page_size)
        self._list_fetch()

    def next_pg(self):
        self.list_offset += self.list_page_size
        self._list_fetch()


class SingleModelInstancePage(tkinter.Frame):
     
    def __init__(self, parent, controller, item=None): 
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.item:SingleModel = None
        self.item_id = '-'

    def _set_item(self, item):
        self.item = item
        self.item_id = getattr(item, 'id', '-')

    def _draw(self):
        for widget in self.winfo_children():
            widget.destroy()

        back_button = ttk.Button(self, text='<-', command=lambda: self.controller.show_frame_str('SingleModelIndexPage'))
        back_button.grid(row=0, column=0)


        label = ttk.Label(self, text=f'single model - {self.item_id}', font=Fonts.heading1)
        label.grid(row=0, column=1)

        field_grid = tkinter.Text(self, font=Fonts.text, wrap='word', height=500, width=100, highlightthickness=0)
        for n, field_name in enumerate(['id'] + field_list):
            field_value = getattr(self.item, field_name, '-')
            if isinstance(field_value, list):
                field_value = ', '.join([str(v) for v in field_value])
            field_display = f'{field_name}:'
            field_grid.insert(tkinter.END, f'{field_display:<{longest_field_name_length + 2}} {field_value}\n\n')
        field_grid.grid(row=1, column=0, columnspan=2)

    def on_show_frame(self, item=None, **kwargs):
        self._set_item(item)
        print(f'Showing SingleModelInstancePage for item: {self.item_id}')
        self._draw()
