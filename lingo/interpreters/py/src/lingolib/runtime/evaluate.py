from lingolib.context import LingoContext
from lingolib.runtime.expressions import unwrap_expression
from lingolib.parsing import LingoASTExeSpec


def execute_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec):
    return unwrap_expression(ctx, ast.main.expr)

