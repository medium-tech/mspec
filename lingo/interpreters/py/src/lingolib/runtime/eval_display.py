import tkinter
import json
import webbrowser

from typing import Callable
from tkinter import messagebox


from lingolib.constants import *
from lingolib.context import LingoContext, LingoStateRuntimeContext
from lingolib.errors import LingoUnknownSymbolError, LingoRuntimeError
from lingolib.parsing import LingoASTTextSpec, LingoASTGUISpec
from lingolib.runtime.shared import raise_runtime_error
from lingolib.runtime.eval_expression import unwrap_expression, evaluate_expression
from lingolib.runtime.registry import init_registry
from lingolib.types import LingoStyleOptions, value_to_str, LingoLanguageError, error_to_str, LingoPrimitiveTypes
from lingolib.symbols import *

DisplayRuntimeSymbols = L_SYM_break | L_SYM_heading | L_SYM_text | L_SYM_link | L_SYM_value

TK_TABLE_TEXT_TAG = 'table-monospace'
TK_TABLE_HEADER_TAG = 'table-header-monospace'

def _debug_state(ctx: LingoContext):
    if ctx.tk.state:
        print(json.dumps(ctx.tk.state.values, indent=4, sort_keys=True))
    else:
        print(f'{ctx.tk.state=}')

#
# tkinter helpers
#

def _configure_root_window(ctx: LingoContext, window_title: str, window_size: tuple[int, int] = (800, 800)):
    ctx.tk.root.title(window_title)
    ctx.tk.root.geometry(f'{window_size[0]}x{window_size[1]}')
    # ctx.tk.root.configure(background='white')
    
    _configure_menu_bar(ctx)
    ctx.tk.text_widget.pack(fill='both', expand=True)

    _configure_heading_styles(ctx)
    _configure_error_style(ctx)

    ctx.tk.in_text_block = False

def _configure_menu_bar(ctx: LingoContext):
    menubar = tkinter.Menu(ctx.tk.root)

    file_menu = tkinter.Menu(menubar, tearoff=0)
    file_menu.add_command(label='Stop Running File', command=ctx.tk.root.destroy)
    menubar.add_cascade(label='File', menu=file_menu)

    edit_menu = tkinter.Menu(menubar, tearoff=0)
    edit_menu.add_command(label='Copy', command=lambda: ctx.tk.text_widget.event_generate('<<Copy>>'))
    edit_menu.add_command(label='Select All', command=lambda: ctx.tk.text_widget.event_generate('<<SelectAll>>'))
    menubar.add_cascade(label='Edit', menu=edit_menu)

    lingo_menu = tkinter.Menu(menubar, tearoff=0)
    lingo_menu.add_command(
        label='About Lingo',
        command=lambda: messagebox.showinfo('Lingo', 'Lingo Runtime\nTkinter preview window')
    )
    lingo_menu.add_command(
        label='Debug State',
        command=lambda: _debug_state(ctx)
    )
    menubar.add_cascade(label='Lingo', menu=lingo_menu)

    ctx.tk.root.configure(menu=menubar)

# styles #

def _configure_text_style(ctx: LingoContext, style: LingoStyleOptions) -> str:
    tag_name = f'text-bold-{style.bold}-italic-{style.italic}-underline-{style.underline}-color-{style.color}'

    
    weight = 'bold' if style.bold else 'normal'
    slant = 'italic' if style.italic else 'roman'

    text_opts = {
        'font': (TEXT_FONT['font']['family'], TEXT_FONT['font']['size'], weight, slant),
    }

    if style.underline:
        text_opts['underline'] = 1

    if style.color:
        text_opts['foreground'] = style.color

    if style.color == 'white':
        text_opts['background'] = 'black'

    text_opts.update(TEXT_FONT.get('options', {}))

    if tag_name not in ctx.tk.text_widget.tag_names():
        ctx.tk.text_widget.tag_configure(tag_name, **text_opts)

    return tag_name

def _configure_link_style(ctx: LingoContext, url: str) -> str:
    tag_name = f'link-{url}'

    if tag_name not in ctx.tk.text_widget.tag_names():
        ctx.tk.text_widget.tag_configure(tag_name, foreground='blue', underline=True)
        ctx.tk.text_widget.tag_bind(tag_name, '<Button-1>', lambda _event, target=url: webbrowser.open_new_tab(target))

    return tag_name

def _configure_error_style(ctx: LingoContext) -> str:
    font = ERROR_TEXT_FONT['font']
    ctx.tk.text_widget.tag_configure(
        'text-error', 
        foreground='red', 
        font=(font['family'], font['size'], font.get('weight', 'normal'))
    )

def _configure_heading_styles(ctx: LingoContext):
    for level in range(MIN_HEADING_LEVEL, MAX_HEADING_LEVEL + 1):
            heading = HEADING_FONTS[level]
            heading_opts = {'font': (heading['font']['family'], heading['font']['size'])}
            heading_opts.update(heading.get('options', {}))
            ctx.tk.text_widget.tag_configure(f'heading-{level}', **heading_opts)

def _configure_table_styles(ctx: LingoContext):
    
    if TK_TABLE_TEXT_TAG not in ctx.tk.text_widget.tag_names():
        table_text_font = (
            TABLE_TEXT_FONT['font']['family'], 
            TABLE_TEXT_FONT['font']['size'],
            TABLE_TEXT_FONT['font'].get('weight', 'normal'),
        )
        ctx.tk.text_widget.tag_configure(TK_TABLE_TEXT_TAG, font=table_text_font)

    if TK_TABLE_HEADER_TAG not in ctx.tk.text_widget.tag_names():
        table_header_font = (
            TABLE_HEADER_FONT['font']['family'], 
            TABLE_HEADER_FONT['font']['size'],
            TABLE_HEADER_FONT['font'].get('weight', 'normal'),
        )
        ctx.tk.text_widget.tag_configure(TK_TABLE_HEADER_TAG, font=table_header_font)

def _create_table_from_list_of_structs(ctx: LingoContext, symbol:L_SYM_value):

    #
    # init
    #

    if symbol.display.format != 'table':
        raise_runtime_error(symbol, f'Cannot render list of struct values with display format: {symbol.display.format}')

    _configure_table_styles(ctx)

    if ctx.tk.main_block_index != 0:
        ctx.tk.text_widget.insert('end', '\n')

    if len(symbol.display.headers) > 0:
        column_fields:list[str] = [header.field for header in symbol.display.headers]
        column_headers:list[str] = [header.text for header in symbol.display.headers]
    else:
        column_fields:list[str] = symbol.display.columns
        column_headers:list[str] = []

    if len(column_fields) == 0:
        raise_runtime_error(symbol, f'Cannot render list of struct value in text spec with no headers or columns specified.')

    has_col_headers = len(column_headers) > 0

    #
    # normalize rows
    #

    rows:list[dict] = []
    for row_index, row_expr in enumerate(symbol.value):
        try:
            row_value = unwrap_expression(ctx, row_expr)
        except Exception:
            if isinstance(row_expr, L_SYM_value) and row_expr.type == 'struct' and isinstance(row_expr.value, dict):
                row_value = row_expr.value
            elif isinstance(row_expr, dict):
                row_value = row_expr
            else:
                raise_runtime_error(symbol, f'Expected table row at index {row_index} to be struct/dict, got: {type(row_expr).__name__}')

        rows.append(row_value)

    #
    # build cells
    #

    table_cells:list[list[str]] = []
    for row_index, row in enumerate(rows):

        row_cells:list[str] = []
        for field in column_fields:
            
            if field not in row:
                raise_runtime_error(symbol, f'Missing expected table field {field!r} in row at index {row_index}')
            
            row_cells.append(value_to_str(unwrap_expression(ctx, row[field])))

        table_cells.append(row_cells)

    #
    # calculate size
    #

    col_widths = []
    for col_i, _field_name in enumerate(column_fields):
        header_title = column_headers[col_i] if has_col_headers else ''
        widest_cell = max((len(cells[col_i]) for cells in table_cells), default=0)
        col_widths.append(max(len(header_title), widest_cell))

    #
    # render table
    #

    def border_line() -> str:
        return '•-' + '-•-'.join('-' * width for width in col_widths) + '-•\n'

    def data_line(cells: list[str]) -> str:
        padded_cells = [f'{cell:<{col_widths[i]}}' for i, cell in enumerate(cells)]
        return '| ' + ' | '.join(padded_cells) + ' |\n'

    if has_col_headers:
        ctx.tk.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))
        ctx.tk.text_widget.insert('end', data_line(column_headers), (TK_TABLE_HEADER_TAG,))

    ctx.tk.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))

    for row_cells in table_cells:
        ctx.tk.text_widget.insert('end', data_line(row_cells), (TK_TABLE_TEXT_TAG,))

    ctx.tk.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))

#
# symbol evaluators
#

# text #

def _eval_break(ctx: LingoContext, symbol: L_SYM_break):
    num_breaks = max(MIN_LINE_BREAKS, min(MAX_LINE_BREAKS, symbol.breaks))
    ctx.tk.text_widget.insert('end', '\n' * num_breaks)

def _eval_header(ctx: LingoContext, symbol: L_SYM_heading):
    text_value = unwrap_expression(ctx, symbol.text)
    level_value = max(MIN_HEADING_LEVEL, min(MAX_HEADING_LEVEL, symbol.level))
    pre_spacer = '\n' if ctx.tk.main_block_index != 0 else ''
    ctx.tk.text_widget.insert('end', f'{pre_spacer}{text_value}', (f'heading-{level_value}',))
    ctx.tk.in_text_block = False

def _eval_text(ctx: LingoContext, symbol: L_SYM_text):
    assert isinstance(symbol.style, LingoStyleOptions)

    if not ctx.tk.in_text_block and ctx.tk.main_block_index != 0:
        ctx.tk.text_widget.insert('end', '\n')

    text_value = unwrap_expression(ctx, symbol.text)

    if isinstance(text_value, LingoLanguageError):
        text_to_insert = error_to_str(text_value)
        tag_name = 'text-error'

    elif isinstance(text_value, str):
        text_to_insert = text_value
        tag_name = _configure_text_style(ctx, symbol.style)

    elif isinstance(text_value, LingoPrimitiveTypes):
        text_to_insert = value_to_str(text_value)
        tag_name = _configure_text_style(ctx, symbol.style)

    else:
        raise_runtime_error(symbol, f'Expected string value for text symbol, got: {type(text_value).__name__}')

    
    ctx.tk.text_widget.insert('end', text_to_insert, (tag_name,))
    ctx.tk.in_text_block = True

def _eval_link(ctx: LingoContext, symbol: L_SYM_link):
    text_value = unwrap_expression(ctx, symbol.text) if symbol.text else unwrap_expression(ctx, symbol.link)
    link_value = unwrap_expression(ctx, symbol.link)
    tag_name = _configure_link_style(ctx, link_value)
    ctx.tk.text_widget.insert('end', text_value, (tag_name,))
    ctx.tk.in_text_block = True

def _eval_value(ctx: LingoContext, symbol: L_SYM_value):

    #
    # type str
    #

    ctx.tk.in_text_block = False

    if symbol.type == 'str':
        if not isinstance(symbol.value, str):
            raise_runtime_error(symbol, f'Expected string value for type "str", got: {type(symbol.value).__name__}')

        else:
            ctx.tk.text_widget.insert('end', symbol.value)
            ctx.tk.in_text_block = True

    #
    # ordered or unordered list
    #

    elif symbol.type == 'list' and symbol.element_type == 'str':
        if ctx.tk.main_block_index != 0:
            ctx.tk.text_widget.insert('end', '\n')

        if symbol.display.format in ['bullets', 'numbers']:
            for n, element in enumerate(symbol.value, start=1):
                prefix = '• ' if symbol.display.format == 'bullets' else f'{n}. '
                ctx.tk.text_widget.insert('end', f'{prefix}')

                _eval_text_runtime_symbol(ctx, element)

                ctx.tk.text_widget.insert('end', f'\n')
        else:
            raise_runtime_error(f'Cannot render list value in text spec with display format: {symbol.display.format}')

    #
    # tables
    #

    elif symbol.type == 'list' and symbol.element_type == 'struct':
        _create_table_from_list_of_structs(ctx, symbol)

    #
    # key/value pairs
    #

    elif symbol.type == 'struct':
        ctx.tk.text_widget.insert('end', '\n')
        if symbol.value:
            max_key_length = max(len(str(key)) for key in symbol.value.keys())
            struct_tag = 'struct-monospace'
            if struct_tag not in ctx.tk.text_widget.tag_names():
                ctx.tk.text_widget.tag_configure(struct_tag, font=MONOSPACE_FONT)
            for key, value in symbol.value.items():
                ctx.tk.text_widget.insert('end', f'{str(key):<{max_key_length + 2}} {value_to_str(value)}\n', (struct_tag,))

    else:
        raise_runtime_error(symbol, f'Cannot render value type in text spec with type: {symbol.type} and element type: {symbol.element_type}')

# gui #

def _eval_button(ctx: LingoContext, symbol: L_SYM_button):
    """placeholder button that just prints a msg to console when clicked"""

    #
    # button click handler
    #

    def on_button_click():
        ctx.log.debug(f'Button clicked: {symbol.text} {symbol.call}')

        # init #

        call_parts = symbol.call.split('.')
        if len(call_parts) != 2 or call_parts[0] != 'ops':
            raise_runtime_error(symbol, f'Button call function must be in the form "ops.<function>", got: {symbol.call!r}')

        # get function #

        try:
            registered_func = ctx.tk.registry.ops[call_parts[1]]
        except KeyError:
            raise_runtime_error(symbol, f'Button call function {symbol.call!r} not found in registry.ops')

        # call function #

        function_return = evaluate_expression(ctx, registered_func.ast.func)
        
        ctx.log.debug(f'{registered_func=} {function_return=}')

    #
    # button text
    #

    text_value = unwrap_expression(ctx, symbol.text)
    if not isinstance(text_value, str):
        raise_runtime_error(symbol, f'Expected string value for button text, got: {type(text_value).__name__}')

    #
    # tk button
    #

    button = tkinter.Button(
        ctx.tk.text_widget,
        text=text_value,
        command=on_button_click,
        background=BUTTON_BACKGROUND_COLOR,
        activebackground=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
        activeforeground=BUTTON_TEXT_COLOR,
        borderwidth=BUTTON_BORDER_WIDTH,
        relief=BUTTON_RELIEF,
        highlightthickness=BUTTON_FOCUS_HIGHLIGHT_THICKNESS,
        highlightcolor=BUTTON_FOCUS_HIGHLIGHT_COLOR,
        highlightbackground=BUTTON_FOCUS_HIGHLIGHT_BACKGROUND,
        padx=BUTTON_PADDING_X,
        pady=BUTTON_PADDING_Y,
        cursor=BUTTON_CURSOR,
    )

    ctx.tk.text_widget.window_create('end', window=button, padx=BUTTON_MARGIN_X, pady=BUTTON_MARGIN_Y)

#
# spec dispatch
#

def _eval_text_runtime_symbol(ctx: LingoContext, symbol: DisplayRuntimeSymbols):
    match symbol.L_SYM_NAME:
        case 'break':
            _eval_break(ctx, symbol)
        case 'heading':
            _eval_header(ctx, symbol)
        case 'text':
            _eval_text(ctx, symbol)
        case 'link':
            _eval_link(ctx, symbol)
        case 'value':
            _eval_value(ctx, symbol)
        case _:
            raise LingoUnknownSymbolError(symbol.L_SYM_NAME)

def _eval_gui_runtime_symbol(ctx: LingoContext, symbol: DisplayRuntimeSymbols):
    try:
        _eval_text_runtime_symbol(ctx, symbol)
    except LingoUnknownSymbolError as e:
        match symbol.L_SYM_NAME:
            case 'button':
                _eval_button(ctx, symbol)
            case _:
                raise LingoUnknownSymbolError(symbol.L_SYM_NAME)

#
# spec helpers
#

def _init_root_tk_text_widget():
    return tkinter.Text(wrap='word', padx=12, pady=12, font=(TEXT_FONT['font']['family'], TEXT_FONT['font']['size']))

def _init_runtime_state(ctx: LingoContext, state_symbol: L_SYM_state) -> LingoStateRuntimeContext:
    state_fields = state_symbol.fields
    state_values = {field_name: unwrap_expression(ctx, field_value.default) for field_name, field_value in state_fields.items()}
    return LingoStateRuntimeContext(fields=state_fields, values=state_values)

#
# spec evaluators
#

def _evaluate_display_spec(ctx: LingoContext, ast: LingoASTTextSpec | LingoASTGUISpec) -> Callable[[], None]:

    if isinstance(ast, LingoASTTextSpec):
        symbol_evaluator = _eval_text_runtime_symbol
        spec_name = 'TEXT'
    elif isinstance(ast, LingoASTGUISpec):
        symbol_evaluator = _eval_gui_runtime_symbol
        spec_name = 'GUI'
    else:
        raise LingoRuntimeError(f'Expected AST of type LingoASTTextSpec or LingoASTGUISpec, got: {type(ast).__name__}')

    def render_func():
        for item in ast.block.items:
            try:
                symbol_evaluator(ctx, item)

            except LingoUnknownSymbolError as e:
                raise_runtime_error(item, f'Unknown symbol "{e}" in {spec_name} spec at index {ctx.tk.main_block_index}')

            except LingoRuntimeError:
                raise

            except Exception as e:
                raise_runtime_error(item, f'Error evaluating {spec_name} block item {ctx.tk.main_block_index}: {e}')

            ctx.tk.main_block_index += 1

    return render_func

def evaluate_text_spec(ctx: LingoContext, ast: LingoASTTextSpec):

    ctx = LingoContext.add_tk_runtime_context(
        ctx, 
        root=tkinter.Tk(), 
        text_widget=_init_root_tk_text_widget()
    )

    _configure_root_window(ctx, window_title='Lingo Text Spec')

    render = _evaluate_display_spec(ctx, ast)
    render()

    ctx.tk.root.mainloop()
    ctx.log.debug('Text spec evaluation complete, exiting mainloop')

def evaluate_gui_spec(ctx: LingoContext, ast: LingoASTGUISpec):

    ctx = LingoContext.add_tk_runtime_context(
        ctx, 
        root=tkinter.Tk(), 
        text_widget=_init_root_tk_text_widget(),
        state=_init_runtime_state(ctx, ast.state) if ast.state else None
    )

    init_registry(ctx, ast.ops)


    _configure_root_window(ctx, window_title='Lingo GUI Spec')

    render = _evaluate_display_spec(ctx, ast)
    render()

    ctx.tk.root.mainloop()
    ctx.log.debug('GUI spec evaluation complete, exiting mainloop')