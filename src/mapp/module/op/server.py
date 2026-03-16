import io
import re
import json

from mimetypes import guess_type
from urllib.parse import parse_qs

from multipart import parse_form_data, is_form_request, MultipartPart, parse_options_header

from mapp.context import MappContext, OpRouteContext, RequestContext
from mapp.types import JSONResponse, DownloadFileResponse, new_op_classes, json_to_op_params_w_convert, convert_dict_to_op_params
from mapp.module.op.run import op_create_callable


def create_op_routes(module_spec:dict, op_spec:dict) -> callable:

    params_class, output_class = new_op_classes(op_spec, module_spec)
    op_kebab_case = op_spec['name']['kebab_case']
    module_kebab_case = module_spec['name']['kebab_case']

    op_ctx = OpRouteContext(
        params_class=params_class,
        output_class=output_class,
        op_kebab_case=op_kebab_case,
        module_kebab_case=module_kebab_case,
        api_op_regex=rf'/api/{module_kebab_case}/{op_kebab_case}',
        run_op=op_create_callable(params_class, output_class)
    )

    route_resolver = lambda server, request: op_route(op_ctx, server, request)
    return route_resolver

def op_route(route: OpRouteContext, server: MappContext, request: RequestContext):
    
    if re.match(route.api_op_regex, request.env['PATH_INFO']):
        input_file_content = None
        content_type, options = parse_options_header(request.env["CONTENT_TYPE"])

        if content_type == 'multipart/form-data' and 'boundary' in options:
            
            forms, files = parse_form_data(request.env)
            json_body = forms.get('json', '{}')

            server.log(f'PROCESSING MULTIPART REQUEST - {list(forms.keys())} - {list(files.keys())}')

            input_file:MultipartPart = files.get('file', None)
            if input_file is not None:
                input_file_content = input_file.file.read()
        
        else:
            json_body = request.raw_req_body.decode('utf-8')

        req_method = request.env['REQUEST_METHOD']
        server.self = {
            'file_input': input_file_content,
            'file_output': io.BytesIO()
        }

        if req_method == 'GET':
            parsed = parse_qs(request.env['QUERY_STRING'])
            query_params = {key: parsed[key][0] for key in parsed}
            
            op_params = convert_dict_to_op_params(route.params_class, query_params)
            op_output = route.run_op(server, op_params)

            try:
                # if file_output_name was set, then we have a file to download
                # all others are assumed to be json responses
                file_output_name = server.self['file_output_name']

            except KeyError:
                server.log(f'GET {route.module_kebab_case}.{route.op_kebab_case}')
                raise JSONResponse('200 OK', op_output)
            
            else:
                raise DownloadFileResponse(
                    content=server.self['file_output'].read(),
                    content_type=guess_type(file_output_name)[0] or 'application/octet-stream',
                    filename=file_output_name
                )
        
        elif req_method == 'POST':
            op_params = json_to_op_params_w_convert(json_body, route.params_class)
            op_output = route.run_op(server, op_params)

            try:
                # if file_output_name was set, then we have a file to download
                # all others are assumed to be json responses
                file_output_name = server.self['file_output_name']

            except KeyError:
                server.log(f'POST {route.module_kebab_case}.{route.op_kebab_case}')
                raise JSONResponse('200 OK', op_output)
            
            else:
                raise DownloadFileResponse(
                    content=server.self['file_output'].read(),
                    content_type=guess_type(file_output_name)[0] or 'application/octet-stream',
                    filename=file_output_name
                )
        
        else:
            server.log(f'ERROR 405 - Invalid Method {req_method} - {route.module_kebab_case}.{route.op_kebab_case}')
            raise JSONResponse('405 Method Not Allowed', {'error': 'Invalid request method'})