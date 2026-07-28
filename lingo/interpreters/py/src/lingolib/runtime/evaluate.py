from lingolib.context import LingoContext
from lingolib.runtime.expressions import unwrap_expression
from lingolib.parsing import LingoASTExeSpec

__all__ = [
	'evaluate_exe_spec',
	'evaluate_text_spec',
]


def evaluate_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return unwrap_expression(ctx, ast.main.expr)

def evaluate_text_spec(ctx: LingoContext, ast: LingoASTExeSpec):
	print('placeholder for evaluate_text_spec')