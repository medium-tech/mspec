from mapp import auth
from mapp.context import MappContext
from mapp.errors import MappError
from mapp.types import validate_op_params, validate_op_output

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

	# create op logic callable #

	try:
		py_definition = param_class._op_spec['python']
		py_call = py_definition['call']
	except KeyError:
		raise MappError('INVALID_OP_SPEC', f'Missing python.call for op {op_snake_case}')
	
	match py_call:
		case 'auth.create_user':
			op_callable = auth.create_user
		case 'auth.login_user':
			op_callable = auth.login_user
		case 'auth.current_user':
			op_callable = auth.current_user
		case 'auth.logout_user':
			op_callable = auth.logout_user
		case 'auth.delete_user':
			op_callable = auth.delete_user
		case _:
			raise MappError('UNKNOWN_OP_CALL', f'Unknown op python.call: {py_call}')
		
	# create application wrapper #

	def run_op(ctx: MappContext, params:object) -> object:
		
		validate_op_params(param_class, params)

		op_output = op_callable(ctx, params)

		return validate_op_output(output_class, op_output)

	return run_op
