#!/usr/bin/env python3
import tkinter
import webbrowser
from tkinter import ttk
from mspec.markup import lingo_app, example_spec, render_output, lingo_execute, lingo_update_state

HEADING = {
    1: ('Verdana', 35),
    2: ('Verdana', 30),
    3: ('Verdana', 25),
    4: ('Verdana', 20),
    5: ('Verdana', 18),
    6: ('Verdana', 16),
}

TEXT = ('Verdana', 12)

    
class LingoPage(tkinter.Frame):
     
    def __init__(self, parent, spec:dict): 
        super().__init__(parent)

        self._text_buffer:tkinter.Text = None
        self._text_row = 0
        self.link_count = 0

        self.app = lingo_app(spec)
        self.render_output()

    def _tk_row(self):
        return f'{self._text_row}.end'
    
    def render_output(self):
        doc = render_output(lingo_update_state(self.app))

        self._text_buffer = tkinter.Text(self, font=TEXT, wrap='word', height=25, width=100, highlightthickness=0)
        self._text_row = 1
        self.link_count = 0
        self.entries = {}

        for n, element in enumerate(doc):
            if 'heading' in element:
                self.render_heading(element)
            elif 'link' in element:
                self.render_link(element)
            elif 'button' in element:
                self.render_button(element)
            elif 'break' in element:
                self.render_break(element)
            elif 'input' in element:
                self.render_input(element)
            elif 'text' in element:
                self.render_text(element)
            else:
                raise ValueError('Unknown element type')
            
            self._text_row += 1
        
        self._text_buffer.grid(row=0, column=0, padx=0)
        self._text_buffer.tag_configure('heading-1', font=HEADING[1])
        self._text_buffer.tag_configure('heading-2', font=HEADING[2])
        self._text_buffer.tag_configure('heading-3', font=HEADING[3])
        self._text_buffer.tag_configure('heading-4', font=HEADING[4])
        self._text_buffer.tag_configure('heading-5', font=HEADING[5])
        self._text_buffer.tag_configure('heading-6', font=HEADING[6])
        self._text_buffer.config(state=tkinter.DISABLED)

    def render_heading(self, element:dict):
        self._text_buffer.insert(self._tk_row(), element['heading'], (f'heading-{element["level"]}'))
        self._text_buffer.insert(self._tk_row(), '\n')

    def render_text(self, element:dict):
        self._text_buffer.insert(self._tk_row(), element['text'])

    def render_break(self, element:dict):
        self._text_buffer.insert(self._tk_row(), '\n' * element['break'])

    def render_button(self, element:dict):
        def on_click():
            print(f'button clicked: {element["text"]}')
            lingo_execute(self.app, element['button'])
            self.render_output()
            
        button = ttk.Button(self._text_buffer, text=element['text'], command=on_click)
        self._text_buffer.window_create(self._tk_row(), window=button)

    def render_input(self, element:dict):

        try:
            state_field_name = list(element['bind']['state'].keys())[0]
        except (KeyError, IndexError):
            raise ValueError('Input element must bind to a state state')
        
        field_type = self.app.spec['state'][state_field_name]['type']
        if field_type == 'str':
            convert = lambda x: x
        elif field_type == 'int':
            convert = lambda x: int(x)
        elif field_type == 'float':
            convert = lambda x: float(x)
        elif field_type == 'bool':
            convert = lambda x: bool(x)
        else:
            raise ValueError(f'Input element cannot bind to unknown state field type: {field_type}')
        
        if state_field_name not in self.app.state:
            raise ValueError(f'Input element cannot bind to unknown state field: {state_field_name}')

        str_variable = tkinter.StringVar()
        def my_callback(*args):
            value = convert(str_variable.get())
            print(f'setting state.{state_field_name} to: {value}')
            self.app.state[state_field_name] = value
            self.render_output()

        str_variable.set(self.app.state[state_field_name])
        str_variable.trace_add('write', my_callback)
        
        entry = tkinter.Entry(
            self._text_buffer, 
            width=element.get('width', 25), 
            borderwidth=1, 
            relief='solid',
            textvariable=str_variable,
        )
        entry.bind('<Return>', lambda *args: my_callback(*args))
        
        self._text_buffer.window_create(self._tk_row(), window=entry)

    def render_link(self, element:dict):
        try:
            display_text = element['text']
        except KeyError:
            display_text = element['link']

        tag = f'link-{self.link_count}'
        self._text_buffer.insert(self._tk_row(), display_text, (tag,))
        self._text_buffer.tag_configure(tag, foreground='blue', underline=1)

        on_click = lambda _button_press: self._open_link(_button_press, element['link'])
        self._text_buffer.tag_bind(tag, '<Button-1>', on_click)

        self.link_count += 1

    def _open_link(self, _button_press, link):
        print(link)
        webbrowser.open_new(link)


class LingoGUIApp(tkinter.Tk):

    def __init__(self, spec:dict):
        super().__init__()
        self.title('Browser2.0')
        self.geometry('1000x800')
        self.configure(background='white')
  
        self.page = LingoPage(self, spec)
        self.page.grid(row=0, column=0, sticky='nsew')
        self.page.tkraise()



if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Run Browser2.0')
    parser.add_argument('--spec', type=str, help='Path to the spec file')
    args = parser.parse_args()
    if args.spec:
        with open(args.spec, 'r') as f:
            spec = json.load(f)
    else:
        spec = example_spec

    app = LingoGUIApp(spec)
    app.mainloop()
