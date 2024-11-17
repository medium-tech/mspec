import tkinter
from tkinter import ttk

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
        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item', font=LARGEFONT)
        label.grid(row=0, column=1)

        # tabs = ttk.Notebook(parent)
        # tabs.add(self._list_tab(tabs), text='list')
        # tabs.add(self._create_tab(tabs), text='create')
        # tabs.grid(row=1, column=0, sticky='nsew')

        list_frame = self._list_tab(self)
        list_frame.grid(row=1, column=1, columnspan=3, sticky='nsew')

    def _list_tab(self, tabs):
        list_tab = ttk.Frame(tabs)

        # vars :: {"['id', 'description', 'verified', 'color', 'count', 'score', 'tags']": "macro.py_field_list(model.fields)"}
        field_names = ['id', 'description', 'verified', 'color', 'count', 'score', 'tags']

        offset = 0
        page_size = 25
        example_items = client_list_example_item(self.controller.ctx, offset=offset, limit=page_size)

        pagination_label = ttk.Label(list_tab, text=f'offset: {offset} limit: {page_size} results: {len(example_items)}')
        pagination_label.grid(row=2, column=0, columnspan=len(field_names), sticky='w')

        status_label = ttk.Label(list_tab, text='status: ok')
        status_label.grid(row=2, column=0, columnspan=len(field_names), sticky='e')

        for n, field_name in enumerate(field_names):
            header = ttk.Label(list_tab, text=field_name)
            header.grid(row=3, column=n)

        for n, example_item in enumerate(example_items):

            id_label = ttk.Label(list_tab, text=example_item.get('id', '-'))
            id_label.grid(row=n + 4, column=0)

            description_label = ttk.Label(list_tab, text=example_item['description'])
            description_label.grid(row=n + 4, column=1)

            verified_label = ttk.Label(list_tab, text=str(example_item['verified']).lower())
            verified_label.grid(row=n + 4, column=2)

            color_label = ttk.Label(list_tab, text=example_item['color'])
            color_label.grid(row=n + 4, column=3)

            count_label = ttk.Label(list_tab, text=str(example_item['count']))
            count_label.grid(row=n + 4, column=4)

            score_label = ttk.Label(list_tab, text=str(example_item['score']))
            score_label.grid(row=n + 4, column=5)

            tags_label = ttk.Label(list_tab, text=', '.join(example_item['tags']))
            tags_label.grid(row=n + 4, column=6)

        return list_tab

    def _create_tab(self, tabs):
        create_tab = ttk.Frame(tabs)
        label = ttk.Label(create_tab, text='create example item')
        label.grid(row=0, column=1)
        return create_tab


class ExampleItemInstancePage(tkinter.Frame):
     
    def __init__(self, parent, controller): 
        super().__init__(parent)

        back_button = ttk.Button(self, text='<-', command=lambda: controller.show_frame_str('SampleModuleIndexPage'))
        back_button.grid(row=0, column=0)

        label = ttk.Label(self, text='example item - <id>', font=LARGEFONT)
        label.grid(row=0, column=1) 
