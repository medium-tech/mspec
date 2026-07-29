import tkinter

from lingolib.context import LingoContext
from lingolib.parsing import LingoASTTextSpec
from lingolib.runtime.expressions import unwrap_expression


def evaluate_text_spec(ctx: LingoContext, ast: LingoASTTextSpec):
    root = tkinter.Tk()
    root.title('Lingo Text Spec')
    root.geometry('700x400')

    text_widget = tkinter.Text(root, wrap='word', padx=12, pady=12, font=('Verdana', 12))
    text_widget.pack(fill='both', expand=True)

    for n, item in enumerate(ast.block.items):
        try:
            if item.L_SYM_NAME == 'break':
                text_widget.insert('end', '\n' * int(unwrap_expression(ctx, item.breaks)))
                continue

            if item.L_SYM_NAME == 'heading':
                text_value = unwrap_expression(ctx, item.text)
                level = unwrap_expression(ctx, item.level) if item.level is not None else 1
                prefix = '#' * int(level)
                text_widget.insert('end', f'{prefix} {text_value}\n\n')
                continue

            text_value = unwrap_expression(ctx, item.text)
        except Exception as exc:
            raise RuntimeError(f'Error evaluating text block item {n}: {exc}') from exc

        text_widget.insert('end', f'{text_value}\n')

    text_widget.configure(state='disabled')
    root.mainloop()