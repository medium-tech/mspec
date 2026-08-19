from lingolib.context import LingoContext
from lingolib.parsing import LingoASTExeSpec
from lingolib.runtime.eval_expression import unwrap_expression
from lingolib.runtime.registry import init_registry, add_lib_to_registry, add_params_to_registry


def evaluate_exe_spec(ctx: LingoContext, ast: LingoASTExeSpec, cli_args: list[str] = []):
    init_registry(ctx)
    add_lib_to_registry(ctx, ast.imports)
    add_params_to_registry(ctx, ast.params, cli_args)
    return unwrap_expression(ctx, ast.main.expr)