import tkinter

from lingolib.context import LingoContext
from lingolib.runtime.expressions import unwrap_expression
from lingolib.runtime.eval_display import evaluate_text_spec
from lingolib.parsing import LingoASTExeSpec, LingoASTTextSpec

__all__ = [
	'evaluate_exe_spec',
	'evaluate_text_spec',
]


def evaluate_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return unwrap_expression(ctx, ast.main.expr)
