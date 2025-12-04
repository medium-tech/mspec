import re

from mapp.context import MappContext, OpRouteContext, RequestContext
from mapp.errors import RequestError
from mapp.types import JSONResponse, new_op_classes, json_to_op_params_w_convert
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

        if (method := request.env['REQUEST_METHOD']) == 'POST':
            req_body = request.raw_req_body.decode('utf-8')
            op_params = json_to_op_params_w_convert(req_body, route.params_class)
            op_output = route.run_op(server, op_params)
            server.log(f'POST {route.module_kebab_case}.{route.op_kebab_case}')
            raise JSONResponse('200 OK', op_output)
        
        else:
            server.log(f'ERROR 405 - Invalid Method {method} - {route.module_kebab_case}.{route.op_kebab_case}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
