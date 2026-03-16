import uuid
import mimetypes
import traceback

from urllib.request import Request, urlopen
from urllib.error import HTTPError

from mapp.context import MappContext
from mapp.errors import MappError, ServerError, ResponseError
from mapp.types import op_params_to_json, json_to_op_output, new_op_output

__all__ = [
	'http_run_op'
]

def http_run_op(ctx: MappContext, params_class:type, output_class:type, params:object) -> object:

	#
	# init
	#

	module_kebab = params_class._module_spec['name']['kebab_case']
	op_kebab = params_class._op_spec['name']['kebab_case']

	url = f'{ctx.client.host}/api/{module_kebab}/{op_kebab}'
	json_request_body = op_params_to_json(params).encode()

	file_input = ctx.self.get('file_input', None)

	try:
		
		#
		# file upload - multipart request
		#

		if file_input is not None:

			# manually construct multipart request, this currently works but
			# may need to be replaced with something like urllib3.encode_multipart_formdata
			# for standard compliance

			boundary = f'----MappBoundary{uuid.uuid4().hex}'
			headers = ctx.client.headers.copy()
			headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'

			# Prepare multipart body
			parts = []

			# JSON part
			parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="json"\r\nContent-Type: application/json\r\n\r\n{json_request_body.decode()}\r\n')

			# File part
			filename = ctx.self.get('file_input_name', 'file.bin')

			mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
			parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n')
			parts[-1] = parts[-1].encode() + file_input + b'\r\n'

			# End boundary
			parts.append(f'--{boundary}--\r\n')

			# Combine parts
			body = b''
			for part in parts:
				if isinstance(part, str):
					body += part.encode()
				else:
					body += part

			request = Request(url, headers=headers, method='POST', data=body)
		else:

			#
			# regular JSON request
			#

			request = Request(url, headers=ctx.client.headers, method='POST', data=json_request_body)
		
		#
		# send request and handle response
		#

		with urlopen(request) as response:
			content_disposition = response.getheader('Content-Disposition', '')

			if content_disposition.startswith('attachment'):

				# response is a file download #

				try:
					filename = content_disposition.split('filename=')[-1].strip('"')
				except IndexError:
					filename = 'downloaded_file.bin'

				ctx.self['file_output'].write(response.read())

				return new_op_output(output_class, {'result': {'acknowledged': True, 'message': f'Retrieved as: {filename}'}})
			
			else:

				# response is a regular JSON response #

				response_body = response.read().decode('utf-8')
				return json_to_op_output(response_body, output_class)

	except HTTPError as e:
		if e.code >= 500:
			ctx.log(f'Server error when running op via http: {e}\n{traceback.format_exc()}')
			raise ServerError(f'Got {e.code}: {e}')
		else:
			raise ResponseError.from_json(e.read().decode('utf-8'))

	except Exception as e:
		ctx.log(f'Unknown exception when running op via http: {e}\n{traceback.format_exc()}')
		raise MappError('UNKNOWN_ERROR', f'Error running op: {e}')
	
