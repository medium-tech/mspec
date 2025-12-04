from urllib.request import Request, urlopen
from urllib.error import HTTPError

from mapp.context import MappContext
from mapp.errors import MappError, ServerError, ResponseError
from mapp.types import op_params_to_json, json_to_op_output

__all__ = [
	'http_run_op'
]

def http_run_op(cxt: MappContext, params_class:type, output_class:type, params:object) -> object:

	# init #
	
	module_kebab = params_class._module_spec['name']['kebab_case']
	op_kebab = params_class._op_spec['name']['kebab_case']

	url = f'{cxt.client.host}/api/{module_kebab}/{op_kebab}'
	request_body = op_params_to_json(params).encode()

	# send request #

	try:
		request = Request(url, headers=cxt.client.headers, method='POST', data=request_body)
		with urlopen(request) as response:
			response_body = response.read().decode('utf-8')
			return json_to_op_output(response_body, output_class)
		
	except HTTPError as e:
		if e.code >= 500:
			raise ServerError(f'Got {e.code}: {e}')
		
		else:
			raise ResponseError.from_json(e.read().decode('utf-8'))
	
	except Exception as e:
		raise MappError('UNKNOWN_ERROR', f'Error running op: {e}')
	
