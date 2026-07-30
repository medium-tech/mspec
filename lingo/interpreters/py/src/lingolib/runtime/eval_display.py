import tkinter
import webbrowser

from dataclasses import dataclass

from lingolib.constants import (
    MIN_LINE_BREAKS,
    MAX_LINE_BREAKS,
    MIN_HEADING_LEVEL,
    MAX_HEADING_LEVEL,
    HEADING_FONTS,
    TEXT_FONT,
    MONOSPACE_FONT,
    TABLE_HEADER_FONT,
    TABLE_TEXT_FONT,
)
from lingolib.context import LingoContext
from lingolib.parsing import LingoASTTextSpec
from lingolib.runtime.expressions import unwrap_expression
from lingolib.types import LingoStyleOptions, value_to_str, LingoTableHeader
from lingolib.parsing.symbols import *

@dataclass(slots=True)
class LingoTKinterContext:
    root: tkinter.Tk
    text_widget: tkinter.Text
    lingo: LingoContext
    main_block_index: int = 0
    in_text_block: bool = False

DisplayRuntimeSymbols = L_SYM_break | L_SYM_heading | L_SYM_text | L_SYM_link | L_SYM_value

TK_TABLE_TEXT_TAG = 'table-monospace'
TK_TABLE_HEADER_TAG = 'table-header-monospace'

#
# helpers
#

def _configure_text_style(tk_ctx: LingoTKinterContext, style: LingoStyleOptions) -> str:
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

    if tag_name not in tk_ctx.text_widget.tag_names():
        tk_ctx.text_widget.tag_configure(tag_name, **text_opts)

    return tag_name

def _configure_link_style(tk_ctx: LingoTKinterContext, url: str) -> str:
    tag_name = f'link-{url}'

    if tag_name not in tk_ctx.text_widget.tag_names():
        tk_ctx.text_widget.tag_configure(tag_name, foreground='blue', underline=True)
        tk_ctx.text_widget.tag_bind(tag_name, '<Button-1>', lambda _event, target=url: webbrowser.open_new_tab(target))

    return tag_name

def _configure_heading_styles(tk_ctx: LingoTKinterContext):
    for level in range(MIN_HEADING_LEVEL, MAX_HEADING_LEVEL + 1):
            heading = HEADING_FONTS[level]
            heading_opts = {'font': (heading['font']['family'], heading['font']['size'])}
            heading_opts.update(heading.get('options', {}))
            tk_ctx.text_widget.tag_configure(f'heading-{level}', **heading_opts)

def _configure_table_styles(tk_ctx: LingoTKinterContext):
    
    if TK_TABLE_TEXT_TAG not in tk_ctx.text_widget.tag_names():
        table_text_font = (
            TABLE_TEXT_FONT['font']['family'], 
            TABLE_TEXT_FONT['font']['size'],
            TABLE_TEXT_FONT['font'].get('weight', 'normal'),
        )
        tk_ctx.text_widget.tag_configure(TK_TABLE_TEXT_TAG, font=table_text_font)

    if TK_TABLE_HEADER_TAG not in tk_ctx.text_widget.tag_names():
        table_header_font = (
            TABLE_HEADER_FONT['font']['family'], 
            TABLE_HEADER_FONT['font']['size'],
            TABLE_HEADER_FONT['font'].get('weight', 'normal'),
        )
        tk_ctx.text_widget.tag_configure(TK_TABLE_HEADER_TAG, font=table_header_font)

def _create_table_from_list_of_structs(tk_ctx: LingoTKinterContext, symbol:L_SYM_value):

    #
    # init
    #

    if symbol.display.format != 'table':
        raise RuntimeError(f'Cannot render list of struct value in text spec with display format: {symbol.display.format}')

    _configure_table_styles(tk_ctx)

    if tk_ctx.main_block_index != 0:
        tk_ctx.text_widget.insert('end', '\n')

    headers:list[LingoTableHeader] = symbol.display.headers
    if len(headers) == 0:
        raise RuntimeError('Table display format requires one or more headers')

    #
    # normalize rows
    #

    rows:list[dict] = []
    for row_index, row_expr in enumerate(symbol.value):
        try:
            row_value = unwrap_expression(tk_ctx.lingo, row_expr)
        except Exception:
            if isinstance(row_expr, L_SYM_value) and row_expr.type == 'struct' and isinstance(row_expr.value, dict):
                row_value = row_expr.value
            elif isinstance(row_expr, dict):
                row_value = row_expr
            else:
                raise RuntimeError(f'Expected table row at index {row_index} to be struct/dict, got: {type(row_expr).__name__}')

        rows.append(row_value)

    #
    # build cells
    #

    table_cells:list[list[str]] = []
    for row_index, row in enumerate(rows):

        row_cells:list[str] = []
        for header in headers:
            if header.field not in row:
                raise RuntimeError(f'Missing expected table field {header.field!r} in row at index {row_index}')
            
            row_cells.append(value_to_str(unwrap_expression(tk_ctx.lingo, row[header.field])))

        table_cells.append(row_cells)

    #
    # calculate size
    #

    header_titles = [header.text for header in headers]

    col_widths = []
    for col_i, title in enumerate(header_titles):
        widest_cell = max((len(cells[col_i]) for cells in table_cells), default=0)
        col_widths.append(max(len(title), widest_cell))

    #
    # render table
    #

    def border_line() -> str:
        return '•-' + '-•-'.join('-' * width for width in col_widths) + '-•\n'

    def data_line(cells: list[str]) -> str:
        padded_cells = [f'{cell:<{col_widths[i]}}' for i, cell in enumerate(cells)]
        return '| ' + ' | '.join(padded_cells) + ' |\n'

    tk_ctx.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))
    tk_ctx.text_widget.insert('end', data_line(header_titles), (TK_TABLE_HEADER_TAG,))
    tk_ctx.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))
    for row_cells in table_cells:
        tk_ctx.text_widget.insert('end', data_line(row_cells), (TK_TABLE_TEXT_TAG,))
    tk_ctx.text_widget.insert('end', border_line(), (TK_TABLE_TEXT_TAG,))

    

#
# symbol evaluators
#

def _eval_break(tk_ctx: LingoTKinterContext, symbol: L_SYM_break):
    num_breaks = max(MIN_LINE_BREAKS, min(MAX_LINE_BREAKS, symbol.breaks))
    tk_ctx.text_widget.insert('end', '\n' * num_breaks)

def _eval_header(tk_ctx: LingoTKinterContext, symbol: L_SYM_heading):
    text_value = unwrap_expression(tk_ctx.lingo, symbol.text)
    level_value = max(MIN_HEADING_LEVEL, min(MAX_HEADING_LEVEL, symbol.level))
    pre_spacer = '\n' if tk_ctx.main_block_index != 0 else ''
    tk_ctx.text_widget.insert('end', f'{pre_spacer}{text_value}', (f'heading-{level_value}',))

def _eval_text(tk_ctx: LingoTKinterContext, symbol: L_SYM_text):
    if not tk_ctx.in_text_block and tk_ctx.main_block_index != 0:
        tk_ctx.text_widget.insert('end', '\n')

    text_value = unwrap_expression(tk_ctx.lingo, symbol.text)
    assert isinstance(symbol.style, LingoStyleOptions)

    tag_name = _configure_text_style(tk_ctx, symbol.style)
    tk_ctx.text_widget.insert('end', text_value, (tag_name,))

def _eval_link(tk_ctx: LingoTKinterContext, symbol: L_SYM_link):
    text_value = unwrap_expression(tk_ctx.lingo, symbol.text) if symbol.text else unwrap_expression(tk_ctx.lingo, symbol.link)
    link_value = unwrap_expression(tk_ctx.lingo, symbol.link)
    tag_name = _configure_link_style(tk_ctx, link_value)
    tk_ctx.text_widget.insert('end', text_value, (tag_name,))

def _eval_value(tk_ctx: LingoTKinterContext, symbol: L_SYM_value):

    #
    # type str
    #

    if symbol.type == 'str':
        if not isinstance(symbol.value, str):
            raise RuntimeError(f'Expected string value for type "str", got: {type(symbol.value).__name__}')

        else:
            tk_ctx.text_widget.insert('end', symbol.value)

    #
    # ordered or unordered list
    #

    elif symbol.type == 'list' and symbol.element_type == 'str':
        if tk_ctx.main_block_index != 0:
            tk_ctx.text_widget.insert('end', '\n')

        if symbol.display.format in ['bullets', 'numbers']:
            for n, element in enumerate(symbol.value, start=1):
                prefix = '• ' if symbol.display.format == 'bullets' else f'{n}. '
                tk_ctx.text_widget.insert('end', f'{prefix}')

                _eval_display_runtime_symbol(tk_ctx, element)

                tk_ctx.text_widget.insert('end', f'\n')
        else:
            raise RuntimeError(f'Cannot render list value in text spec with display format: {symbol.display.format}')

    #
    # tables
    #

    elif symbol.type == 'list' and symbol.element_type == 'struct':
        _create_table_from_list_of_structs(tk_ctx, symbol)

    #
    # key/value pairs
    #

    elif symbol.type == 'struct':
        tk_ctx.text_widget.insert('end', '\n')
        if symbol.value:
            max_key_length = max(len(str(key)) for key in symbol.value.keys())
            struct_tag = 'struct-monospace'
            if struct_tag not in tk_ctx.text_widget.tag_names():
                tk_ctx.text_widget.tag_configure(struct_tag, font=MONOSPACE_FONT)
            for key, value in symbol.value.items():
                tk_ctx.text_widget.insert('end', f'{str(key):<{max_key_length + 2}} {value_to_str(value)}\n', (struct_tag,))

    else:
        raise RuntimeError(f'Cannot render value type in text spec with type: {symbol.type} and element type: {symbol.element_type}')

def _eval_display_runtime_symbol(tk_ctx: LingoTKinterContext, symbol: DisplayRuntimeSymbols):
    match symbol.L_SYM_NAME:
        case 'break':
            _eval_break(tk_ctx, symbol)
        case 'heading':
            _eval_header(tk_ctx, symbol)
        case 'text':
            _eval_text(tk_ctx, symbol)
        case 'link':
            _eval_link(tk_ctx, symbol)
        case 'value':
            _eval_value(tk_ctx, symbol)
        case _:
            raise RuntimeError(f'Cannot render symbol in text spec: {symbol.L_SYM_NAME}')

#
# spec evaluators
#

def evaluate_text_spec(ctx: LingoContext, ast: LingoASTTextSpec):

    tkinter_ctx = LingoTKinterContext(
        root=tkinter.Tk(),
        text_widget=tkinter.Text(wrap='word', padx=12, pady=12, font=(TEXT_FONT['font']['family'], TEXT_FONT['font']['size'])),
        lingo=ctx,
    )

    root = tkinter_ctx.root
    root.title('Lingo Text Spec')
    root.geometry('800x1200')

    text_widget = tkinter_ctx.text_widget
    text_widget.pack(fill='both', expand=True)

    _configure_heading_styles(tkinter_ctx)

    tkinter_ctx.in_text_block = False

    for item in ast.block.items:
        try:
            _eval_display_runtime_symbol(tkinter_ctx, item)

        except Exception as exc:
            raise RuntimeError(f'Error evaluating text block item {tkinter_ctx.main_block_index}: {exc}')

        tkinter_ctx.in_text_block = item.L_SYM_NAME in ('text', 'link')
        tkinter_ctx.main_block_index += 1
        
    text_widget.configure(state='disabled')
    root.mainloop()
