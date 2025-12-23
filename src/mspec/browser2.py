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
MONOSPACE = ('Courier New', 12)

    
class LingoPage(tkinter.Frame):
     
    def __init__(self, parent, spec:dict): 
        super().__init__(parent)

        self._text_buffer:tkinter.Text = None
        self._text_row = 0
        self._inserted_text_on_current_line = False
        self.link_count = 0
        self.style_count = 0

        self.app = lingo_app(spec)
        self.render_output()

    def _tk_row(self):
        return f'{self._text_row}.end'
    
    def _insert(self, index, chars, *args):
        """Wrapper around text_buffer.insert that tracks text insertion on current line"""
        self._text_buffer.insert(index, chars, *args)
        # Only mark as having text if we're inserting non-empty content that's not just newlines
        if chars and chars.strip():
            self._inserted_text_on_current_line = True
    
    def _new_line(self):
        """Move to a new line and reset text tracking"""
        self._text_row += 1
        self._inserted_text_on_current_line = False
    
    def _element_break(self):
        """Insert a line break only if the current line has text"""
        if self._inserted_text_on_current_line:
            self._text_buffer.insert(self._tk_row(), '\n')
            self._new_line()
    
    def render_output(self):
        doc = render_output(lingo_update_state(self.app))

        self._text_buffer = tkinter.Text(self, font=TEXT, wrap='word', height=50, width=100, highlightthickness=0, borderwidth=2, relief='solid')
        self._text_row = 1
        self._inserted_text_on_current_line = False
        self.link_count = 0
        self.style_count = 0
        self.entries = {}

        for n, element in enumerate(doc):
            try:
                self.render_element(element)
            except Exception as e:
                raise RuntimeError(f'Error rendering output #{n}: {element}') from e
            
            self._new_line()
        
        self._text_buffer.grid(row=0, column=0, padx=0)
        self._text_buffer.tag_configure('heading-1', font=HEADING[1])
        self._text_buffer.tag_configure('heading-2', font=HEADING[2])
        self._text_buffer.tag_configure('heading-3', font=HEADING[3])
        self._text_buffer.tag_configure('heading-4', font=HEADING[4])
        self._text_buffer.tag_configure('heading-5', font=HEADING[5])
        self._text_buffer.tag_configure('heading-6', font=HEADING[6])
        self._text_buffer.tag_configure('monospace', font=MONOSPACE)
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
        self._insert(self._tk_row(), element['heading'], (f'heading-{element["level"]}'))
        self._insert(self._tk_row(), '\n')

    def render_text(self, element:dict):
        text = element['text']

        # Check if styling is present
        if 'style' in element:
            style = element['style']
            tag = f'style-{self.style_count}'
            self._insert(self._tk_row(), text, (tag,))

            # Configure tag with styling
            tag_config = {}

            # Font weight and slant - always set to ensure consistent baseline
            font_family, font_size = TEXT
            weight = 'bold' if style.get('bold') else 'normal'
            slant = 'italic' if style.get('italic') else 'roman'
            tag_config['font'] = (font_family, font_size, weight, slant)

            # Text decoration - can combine underline and strikethrough
            if style.get('underline'):
                tag_config['underline'] = 1
            if style.get('strikethrough'):
                tag_config['overstrike'] = 1

            # Color - handle special color name conversions
            if 'color' in style:
                color = style['color']
                # Convert specific underscore color names to tkinter format
                if color == 'dark_gray':
                    color = 'darkgray'
                elif color == 'light_gray':
                    color = 'lightgray'
                tag_config['foreground'] = color

            self._text_buffer.tag_configure(tag, **tag_config)
            self.style_count += 1
        else:
            self._insert(self._tk_row(), text)

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
                    self._insert(self._tk_row(), bullet_char(n))
                    self.render_element(item)
                    self._new_line()

                    # line break after each item #
                    self._insert(self._tk_row(), '\n')
                    self._new_line()
        else:
            self._insert(self._tk_row(), json.dumps(element, indent=4, sort_keys=True))
    
    def _render_struct(self, element:dict):
        """Render a struct as a table with key-value pairs"""
        fields = element['value']
        show_headers = element.get('display', {}).get('headers', True)

        # Build table data
        rows = []
        max_key_length = 0
        for key, value in fields.items():
            # Evaluate the value if it's a lingo expression
            evaluated_value = self._evaluate_field_value(value)
            rows.append((key, str(evaluated_value)))
            max_key_length = max(max_key_length, len(key))

        col_width = max_key_length + (max_key_length // 4)
        separator = '-' * (col_width * 2)

        self._insert(self._tk_row(), '\n')
        self._new_line()
        
        # Render as table
        if show_headers:
            header_row = f'{"Key": <{col_width}} Value'
            self._insert(self._tk_row(), separator + '\n', ('monospace',))
            self._new_line()
            self._insert(self._tk_row(), header_row + '\n', ('monospace',))
            self._new_line()
            self._insert(self._tk_row(), separator + '\n', ('monospace',))
            self._new_line()
        
        for key, value in rows:
            # Format the row with padding
            key_display = f'{key}:'
            row_text = f'{key_display: <{col_width}} {value}'
            self._insert(self._tk_row(), row_text + '\n', ('monospace',))
            self._new_line()
    
    def _render_table_list(self, element:dict):
        """Render a list of structs as a table"""

        try:
            headers = element['display']['headers']
        except KeyError:
            raise ValueError('Table format list requires display.headers definition')
        
        #
        # evaluate table rows
        #

        rows_data = []
        column_widths = {header_def['field']: len(header_def['text']) for header_def in headers}
        for item in element['value']:
            if not isinstance(item, dict) or item.get('type') != 'struct':
                raise ValueError('All items in a table-formatted list must be structs')
            
            fields = item['value']
            item_data = {}
            for header_def in headers:
                try:
                    field_name = header_def['field']
                    field_value = fields[field_name]
                except KeyError:
                    raise ValueError(f'Field "{field_name}" not found in struct for table row')
                
                # Evaluate the field value
                evaluated_value = self._evaluate_field_value(field_value)
                value_len = len(str(evaluated_value))
                column_widths[field_name] = max(column_widths[field_name], value_len)
                item_data[field_name] = str(evaluated_value)
            
            rows_data.append(item_data)


        # padding to column widths #
        column_widths = {field_name: int(width * 1.3) for field_name, width in column_widths.items()}

        total_width = sum(column_widths.values())
        separator = '-' * total_width

        #
        # render table
        #

        # headers #

        self._insert(self._tk_row(), '\n')
        self._new_line()

        header_text = ''
        for header_def in headers:
            field_name = header_def['field']
            col_width = column_widths[field_name]
            header_text += f'{header_def["text"]: <{col_width}}'

        self._insert(self._tk_row(), separator + '\n', ('monospace',))
        self._new_line()
        self._insert(self._tk_row(), header_text + '\n', ('monospace',))
        self._new_line()
        self._insert(self._tk_row(), separator + '\n', ('monospace',))
        self._new_line()

        # rows #
        for item_data in rows_data:
            row_text = ''
            for header_def in headers:
                field_name = header_def['field']
                col_width = column_widths[field_name]
                row_text += f'{item_data[field_name]: <{col_width}}'
            self._insert(self._tk_row(), row_text + '\n', ('monospace',))
            self._new_line()
    
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
        self._insert(self._tk_row(), '\n' * element['break'])

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
        self._insert(self._tk_row(), display_text, (tag,))
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
