import json
import re

from urllib.parse import parse_qs

from mapp.errors import NotFoundError, RequestError
from mapp.context import MappContext, RequestContext, RouteContext
from mapp.types import JSONResponse, convert_json_to_model, model_to_json, new_model_class
from mapp.module.model.db import *


__all__ = [
    'create_model_routes',
    'model_routes'
]


#
# router
#

def create_model_routes(module_spec:dict, model_spec:dict) -> tuple[callable, type]:
    """
    Take a module and model spec and return a route resolver function for that model along with the model class.
    """
    model_class = new_model_class(model_spec, module_spec)
    model_kebab_case = model_class._model_spec['name']['kebab_case']
    module_kebab_case = model_class._module_spec['name']['kebab_case']

    route_ctx = RouteContext(
        model_class=model_class,
        model_kebab_case=model_kebab_case,
        module_kebab_case=module_kebab_case,
        api_instance_regex=rf'/api/{module_kebab_case}/{model_kebab_case}/(.+)',
        api_model_regex=rf'/api/{module_kebab_case}/{model_kebab_case}'
    )

    route_resolver = lambda server, request: model_routes(route_ctx, server, request)
    return route_resolver, model_class

def model_routes(route: RouteContext, server: MappContext, request: RequestContext):

    #
    # instance routes
    #

    if (instance := re.match(route.api_instance_regex, request.env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)

        # read #

        if request.env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_model_read(server, route.model_class, instance_id)
                server.log(f'GET {route.module_kebab_case}.{route.model_kebab_case}/{instance_id}')
                raise JSONResponse('200 OK', model_to_json(item))
            
            except NotFoundError:
                server.log(f'GET {route.module_kebab_case}.{route.model_kebab_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {route.module_kebab_case}.{route.model_kebab_case}.{instance_id}')

        # update #

        elif request.env['REQUEST_METHOD'] == 'PUT':
            req_body = request.raw_req_body.decode('utf-8')
            incoming_item = convert_json_to_model(route.model_class, req_body, instance_id)

            try:
                updated_item = db_model_update(server, route.model_class, instance_id, incoming_item)
            except NotFoundError:
                server.log(f'PUT {route.module_kebab_case}.{route.model_kebab_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {route.module_kebab_case}.{route.model_kebab_case}.{instance_id}')
            
            server.log(f'PUT {route.module_kebab_case}.{route.model_kebab_case}/{instance_id}')
            raise JSONResponse('200 OK', model_to_json(updated_item))

        # delete #

        elif request.env['REQUEST_METHOD'] == 'DELETE':
            ack = db_model_delete(server, route.model_class, instance_id)
            server.log(f'DELETE {route.module_kebab_case}.{route.model_kebab_case}/{instance_id}')
            raise JSONResponse('204 No Content', ack)
        
        # invalid method #

        else:
            server.log(f'ERROR 405 {route.module_kebab_case}.{route.model_kebab_case}/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    #
    # model routes
    #

    elif re.match(route.api_model_regex, request.env['PATH_INFO']):

        # create #

        if request.env['REQUEST_METHOD'] == 'POST':
            incoming_item = route.model_class(**json.loads(request.raw_req_body.decode('utf-8')))
            item = db_model_create(server, route.model_class, incoming_item)

            server.log(f'POST {route.module_kebab_case}.{route.model_kebab_case} - id: {item.id}')
            raise JSONResponse('200 OK', model_to_json(item))
        
        # list #
        
        elif request.env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(request.env['QUERY_STRING'])
            offset = int(query.get('offset', [0])[0])
            size = int(query.get('size', [25])[0])

            result = db_model_list(server, route.model_class, offset=offset, size=size)
            server.log(f'GET {route.module_kebab_case}.{route.model_kebab_case}')

            raise JSONResponse('200 OK', result)
        
        else:
            server.log(f'ERROR 405 {route.module_kebab_case}.{route.model_kebab_case}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
