from mapp import auth
from mapp.context import MappContext
from mapp.errors import MappError
from mapp.types import validate_op_params, validate_op_output, OpResult
from mspec.lingo import LingoApp, lingo_execute, unwrap_primitive

__all__ = [
	'op_create_callable'
]

def op_create_callable(param_class:type, output_class:type) -> object:
	"""
	Create operation callable from op spec. It is designed so that
	it only needs to be created once at server start time.  The returned
	callable can then be invoked multiple times per request without 
	re-creating the logic each time.

	Currently limited to select builtin ops. In the future,
	lingo spec files or app supplied python code may be used to define
	the operation logic.

	The returned callable:

		Args:
			ctx: MappContext		(context created by server, cli, etc)
			params: object 			(op params object as defined by op spec)

		Returns:
			object:					(op output object as defined by op spec)

		Raises:
			MappValidationError: 	if params or output do not validate
			Exception:				Any other exception raised by the op logic.

	"""


	op_snake_case = param_class._op_spec['name']['snake_case']

	#
	# init
	#

	if 'python' in param_class._op_spec:
		raise MappError('DEPRECATED_OP_SPEC', f'Op {op_snake_case} uses deprecated python op spec. Please update to use func.')
	
	try:
		lingo_func = param_class._op_spec['func']
	except KeyError:
		raise MappError('INVALID_OP_SPEC', f'Op {op_snake_case} missing lingo func in op spec.')

	def op_callable(ctx: MappContext, params:object) -> object:
		spec = {'params': param_class._op_spec['params']}
		validate_op_params(param_class, params)
		lingo_app = LingoApp(
			spec,
			params,
			dict(),
			list()
		)

		op_output = lingo_execute(lingo_app, lingo_func, ctx)

		return validate_op_output(output_class, OpResult(unwrap_primitive(op_output)))
		
	# create application wrapper #

	def run_op(ctx: MappContext, params:object) -> object:
		validate_op_params(param_class, params)

		op_output = op_callable(ctx, params)
	
		return validate_op_output(output_class, op_output)

	return run_op
