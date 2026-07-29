import tkinter

from lingolib.constants import (
    MIN_LINE_BREAKS,
    MAX_LINE_BREAKS,
    MIN_HEADING_LEVEL,
    MAX_HEADING_LEVEL,
    HEADING_FONTS
)
from lingolib.context import LingoContext
from lingolib.parsing import LingoASTTextSpec
from lingolib.runtime.expressions import unwrap_expression


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
                continue

            elif item.L_SYM_NAME == 'heading':
                text_value = unwrap_expression(ctx, item.text)
                level_value = max(MIN_HEADING_LEVEL, min(MAX_HEADING_LEVEL, item.level))
                text_widget.insert('end', f'{text_value}\n\n', (f'heading-{level_value}',))
                continue

            elif item.L_SYM_NAME == 'text':
                text_value = unwrap_expression(ctx, item.text)
                text_widget.insert('end', f'{text_value}\n')
                
            else: 
                raise RuntimeError(f'Cannot render symbol in text spec: {item.L_SYM_NAME}')

        except Exception as exc:
            raise RuntimeError(f'Error evaluating text block item {n}: {exc}') from exc

    text_widget.configure(state='disabled')
    root.mainloop()