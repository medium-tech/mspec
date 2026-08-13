"""

allow access to:
- ops parsed from local gui spec
(future features)
- functions loaded from lib spec
- data loaded from data spec
- backed specs from app spec

"""

from lingolib.parsing.symbols import L_SYM_ops
from lingolib.context import LingoRegisteredFunction, LingoRegistry, LingoContext


#
# api
#

def init_registry(ctx: LingoContext):
	if ctx.tk is None:
		raise RuntimeError('LingoContext.tk runtime has not been initialized')

	if ctx.tk.registry is None:
		ctx.tk.registry = LingoRegistry()
	else:
		raise RuntimeError('Runtime registry has already been initialized')

def add_ops_to_registry(ctx: LingoContext, ops: L_SYM_ops):
	if ctx.tk is None or ctx.tk.registry is None:
		raise RuntimeError('LingoContext.tk.registry has not been initialized')

	for op_name, op_func in ops.ops.items():
		ctx.tk.registry.ops[op_name] = LingoRegisteredFunction(name=op_name, ast=op_func)