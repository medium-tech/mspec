from lingolib.context import LingoContext
from lingolib.parsing import LingoASTLibSpec
from lingolib.runtime.registry import add_modules_to_registry

__all__ = [
	'evaluate_lib_spec',
]


def evaluate_lib_spec(ctx: LingoContext, ast: LingoASTLibSpec):
	"""register a lib spec's modules into the runtime registry for use by call/validate/get expressions elsewhere"""
	add_modules_to_registry(ctx, ast.modules)
