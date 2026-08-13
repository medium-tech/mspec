from lingolib.context import LingoContext
from lingolib.parsing import LingoASTExeSpec
from lingolib.runtime.eval_expression import unwrap_expression


def evaluate_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return unwrap_expression(ctx, ast.main.expr)