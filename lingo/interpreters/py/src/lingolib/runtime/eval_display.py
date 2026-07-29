import tkinter

from lingolib.context import LingoContext
from lingolib.runtime.expressions import unwrap_expression
from lingolib.parsing import LingoASTTextSpec

def evaluate_text_spec(ctx: LingoContext, ast: LingoASTTextSpec):
    root = tkinter.Tk()
    root.title('Lingo Text Spec')
    root.geometry('700x400')

    text_widget = tkinter.Text(root, wrap='word', padx=12, pady=12, font=('Verdana', 12))
    text_widget.pack(fill='both', expand=True)

    for n, item in enumerate(ast.block.items):
        try:
            text_value = unwrap_expression(ctx, item.text)
        except Exception as exc:
            raise RuntimeError(f'Error evaluating text block item {n}: {exc}') from exc

        text_widget.insert('end', f'{text_value}\n')

    text_widget.configure(state='disabled')
    root.mainloop()