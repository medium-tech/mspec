import tkinter
import webbrowser

from lingolib.constants import (
    MIN_LINE_BREAKS,
    MAX_LINE_BREAKS,
    MIN_HEADING_LEVEL,
    MAX_HEADING_LEVEL,
    HEADING_FONTS,
    TEXT_FONT,
    MONOSPACE_FONT,
)
from lingolib.context import LingoContext
from lingolib.parsing import LingoASTTextSpec
from lingolib.runtime.expressions import unwrap_expression
from lingolib.types import LingoStyleOptions, value_to_str


def _configure_text_style(text_widget: tkinter.Text, style: LingoStyleOptions) -> str:
    tag_name = f'style-text-bold-{style.bold}-italic-{style.italic}-underline-{style.underline}-color-{style.color}'

    font_family, font_size = TEXT_FONT
    weight = 'bold' if style.bold else 'normal'
    slant = 'italic' if style.italic else 'roman'

    tag_config = {
        'font': (font_family, font_size, weight, slant),
    }

    if style.underline:
        tag_config['underline'] = 1

    if style.color:
        tag_config['foreground'] = style.color

    if style.color == 'white':
        tag_config['background'] = 'black'

    if tag_name not in text_widget.tag_names():
        text_widget.tag_configure(tag_name, **tag_config)

    return tag_name


def _configure_link_style(text_widget: tkinter.Text, url: str) -> str:
    tag_name = f'link-{url}'

    if tag_name not in text_widget.tag_names():
        text_widget.tag_configure(tag_name, foreground='blue', underline=True)
        text_widget.tag_bind(tag_name, '<Button-1>', lambda _event, target=url: webbrowser.open_new_tab(target))

    return tag_name


def evaluate_text_spec(ctx: LingoContext, ast: LingoASTTextSpec):
    root = tkinter.Tk()
    root.title('Lingo Text Spec')
    root.geometry('700x400')

    text_widget = tkinter.Text(root, wrap='word', padx=12, pady=12, font=('Verdana', 12))
    text_widget.pack(fill='both', expand=True)

    for level in range(MIN_HEADING_LEVEL, MAX_HEADING_LEVEL + 1):
        text_widget.tag_configure(f'heading-{level}', font=HEADING_FONTS[level])

    for n, item in enumerate(ast.block.items):
        try:
            if item.L_SYM_NAME == 'break':
                num_breaks = max(MIN_LINE_BREAKS, min(MAX_LINE_BREAKS, item.breaks))
                text_widget.insert('end', '\n' * num_breaks)

            elif item.L_SYM_NAME == 'heading':
                text_value = unwrap_expression(ctx, item.text)
                level_value = max(MIN_HEADING_LEVEL, min(MAX_HEADING_LEVEL, item.level))
                text_widget.insert('end', f'{text_value}\n\n', (f'heading-{level_value}',))

            elif item.L_SYM_NAME == 'text':
                text_value = unwrap_expression(ctx, item.text)
                assert isinstance(item.style, LingoStyleOptions)

                tag_name = _configure_text_style(text_widget, item.style)
                text_widget.insert('end', text_value, (tag_name,))

            elif item.L_SYM_NAME == 'link':
                text_value = unwrap_expression(ctx, item.text) if item.text else unwrap_expression(ctx, item.link)
                link_value = unwrap_expression(ctx, item.link)
                tag_name = _configure_link_style(text_widget, link_value)
                text_widget.insert('end', text_value, (tag_name,))

            elif item.L_SYM_NAME == 'value':
                if item.type == 'list' and item.element_type == 'str':
                    text_widget.insert('end', '\n')
                    for element in item.value:
                        text_widget.insert('end', f'• {element}\n')

                elif item.type == 'struct':
                    text_widget.insert('end', '\n')
                    if item.value:
                        max_key_length = max(len(str(key)) for key in item.value.keys())
                        struct_tag = 'struct-monospace'
                        if struct_tag not in text_widget.tag_names():
                            text_widget.tag_configure(struct_tag, font=MONOSPACE_FONT)
                        for key, value in item.value.items():
                            text_widget.insert('end', f'{str(key):<{max_key_length + 2}} {value_to_str(value)}\n', (struct_tag,))
                else:
                    raise RuntimeError(f'Cannot render value type in text spec with type: {item.type} and element type: {item.element_type}')

            else:
                raise RuntimeError(f'Cannot render symbol in text spec: {item.L_SYM_NAME}')

        except Exception as exc:
            raise RuntimeError(f'Error evaluating text block item {n}: {exc}') from exc

    text_widget.configure(state='disabled')
    root.mainloop()