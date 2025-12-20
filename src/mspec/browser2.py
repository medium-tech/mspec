#!/usr/bin/env python3
import json
import tkinter
import webbrowser
from tkinter import ttk
from mspec.core import SAMPLE_DATA_DIR, load_browser2_spec
from mspec.lingo import lingo_app, render_output, lingo_execute, lingo_update_state

DEFAULT_SPEC = 'test-page.json'

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

        self._text_buffer = tkinter.Text(self, font=TEXT, wrap='word', height=50, width=100, highlightthickness=0, borderwidth=2, relief='solid')
        self._text_row = 1
        self.link_count = 0
        self.entries = {}

        for n, element in enumerate(doc):
            try:
                self.render_element(element)
            except Exception as e:
                raise RuntimeError(f'Error rendering output #{n}: {element}') from e
            
            self._text_row += 1
        
        self._text_buffer.grid(row=0, column=0, padx=0)
        self._text_buffer.tag_configure('heading-1', font=HEADING[1])
        self._text_buffer.tag_configure('heading-2', font=HEADING[2])
        self._text_buffer.tag_configure('heading-3', font=HEADING[3])
        self._text_buffer.tag_configure('heading-4', font=HEADING[4])
        self._text_buffer.tag_configure('heading-5', font=HEADING[5])
        self._text_buffer.tag_configure('heading-6', font=HEADING[6])
        self._text_buffer.config(state=tkinter.DISABLED)

    def render_element(self, element:dict):
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
        elif 'value' in element:
            self.render_value(element)
        else:
            raise ValueError(f'Unknown element type: {list(element)}')

    def render_heading(self, element:dict):
        self._text_buffer.insert(self._tk_row(), element['heading'], (f'heading-{element["level"]}'))
        self._text_buffer.insert(self._tk_row(), '\n')

    def render_text(self, element:dict):
        self._text_buffer.insert(self._tk_row(), element['text'])

    def render_value(self, element:dict):
        if element['type'] == 'struct':
            self._render_struct(element)
        elif element['type'] == 'list':
            
            # init list formatting #
            bullet_format = element.get('display', {}).get('format', 'bullets')
            
            if bullet_format == 'table':
                self._render_table_list(element)
            else:
                match bullet_format:
                    case 'bullets':
                        bullet_char = lambda _: '• '
                    case 'numbers':
                        bullet_char = lambda n: f'{n}. '
                    case _:
                        raise ValueError(f'Unknown list display.format: {bullet_format}')

                for n, item in enumerate(element['value'], start=1):
                    # insert bullet and item #
                    self._text_buffer.insert(self._tk_row(), bullet_char(n))
                    self.render_element(item)
                    self._text_row += 1

                    # line break after each item #
                    self._text_buffer.insert(self._tk_row(), '\n')
                    self._text_row += 1
        else:
            self._text_buffer.insert(self._tk_row(), json.dumps(element, indent=4, sort_keys=True))
    
    def _render_struct(self, element:dict):
        """Render a struct as a table with key-value pairs"""
        fields = element.get('fields', {})
        show_headers = element.get('display', {}).get('headers', True)
        
        # Build table data
        rows = []
        for key, value in fields.items():
            # Evaluate the value if it's a lingo expression
            evaluated_value = self._evaluate_field_value(value)
            rows.append((key, str(evaluated_value)))
        
        # Render as table
        if show_headers:
            header_row = 'key' + ' ' * 20 + 'value'
            separator = '-' * 50
            self._text_buffer.insert(self._tk_row(), header_row + '\n')
            self._text_buffer.insert(self._tk_row(), separator + '\n')
        
        for key, value in rows:
            # Format the row with padding
            row_text = f'{key:<23} {value}'
            self._text_buffer.insert(self._tk_row(), row_text + '\n')
    
    def _render_table_list(self, element:dict):
        """Render a list of structs as a table"""
        headers = element.get('display', {}).get('headers', [])
        items = element.get('value', [])
        
        # Validate all items are structs
        for item in items:
            if not isinstance(item, dict) or item.get('type') != 'struct':
                raise ValueError('All items in a table-formatted list must be structs')
        
        # Build header row
        header_text = ''
        for i, header_def in enumerate(headers):
            header_text += header_def['text']
            if i < len(headers) - 1:
                header_text += ' ' * 10
        
        self._text_buffer.insert(self._tk_row(), header_text + '\n')
        
        # Build separator
        separator = '-' * (len(header_text) + 20)
        self._text_buffer.insert(self._tk_row(), separator + '\n')
        
        # Build data rows
        for item in items:
            fields = item.get('fields', {})
            row_text = ''
            for i, header_def in enumerate(headers):
                field_name = header_def['field']
                field_value = fields.get(field_name, '')
                
                # Evaluate the field value
                evaluated_value = self._evaluate_field_value(field_value)
                
                # Add to row with padding
                col_width = len(header_def['text']) + 10
                row_text += f'{str(evaluated_value):<{col_width}}'
            
            self._text_buffer.insert(self._tk_row(), row_text.rstrip() + '\n')
    
    def _evaluate_field_value(self, value):
        """Evaluate a field value, handling both literals and lingo expressions"""
        if isinstance(value, dict):
            # Check if it's a typed value (e.g., {"type": "str", "value": "green"})
            if 'type' in value and 'value' in value:
                return value['value']
            # Check if it's a lingo expression (e.g., {"call": "add", "args": {...}})
            elif 'call' in value or 'state' in value or 'params' in value or 'op' in value:
                result = lingo_execute(self.app, value)
                if isinstance(result, dict) and 'value' in result:
                    return result['value']
                return result
            else:
                # Unknown dict format, return as-is
                return value
        else:
            # Literal value
            return value

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
    parser.add_argument('--spec', type=str, default=DEFAULT_SPEC, help=f'Path to the spec file, default: {DEFAULT_SPEC}')
    args = parser.parse_args()

    spec = load_browser2_spec(args.spec)
    app = LingoGUIApp(spec)
    app.mainloop()
