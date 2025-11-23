import json
import re

from urllib.parse import parse_qs

from mapp.errors import NotFoundError, RequestError
from mapp.context import MappContext, RequestContext, RouteContext
from mapp.types import JSONResponse, model_to_json, list_to_json, ModelListResult
from mapp.module.model.db import *


__all__ = [
    'create_model_routes',
    'model_routes'
]


#
# router
#

def create_model_routes(model_class:type) -> callable:
    model_snake_case = model_class._model_spec['name']['snake_case']
    module_snake_case = model_class._model_spec['module']['snake_case']

    route_ctx = RouteContext(
        model_class=model_class,
        model_snake_case=model_snake_case,
        module_snake_case=module_snake_case,
        api_instance_regex=rf'/api/{module_snake_case}/{model_snake_case}/(.+)',
        api_model_regex=rf'/api/{module_snake_case}/{model_snake_case}'
    )

    return lambda server, request: model_routes(route_ctx, server, request)

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
                server.log(f'GET {route.module_snake_case}.{route.model_snake_case}/{instance_id}')
                raise JSONResponse('200 OK', model_to_json(item))
            
            except NotFoundError:
                server.log(f'GET {route.module_snake_case}.{route.model_snake_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {route.module_snake_case}.{route.model_snake_case}.{instance_id}')

        # update #

        elif request.env['REQUEST_METHOD'] == 'PUT':
            incoming_item = route.model_class(**json.loads(request.raw_req_body.decode('utf-8')))

            if instance_id != str(incoming_item.id):
                raise RequestError('400 Bad Request', f'{route.model_snake_case} id mismatch')
            try:
                updated_item = db_model_update(server, route.model_class, instance_id, incoming_item)
            except NotFoundError:
                server.log(f'PUT {route.module_snake_case}.{route.model_snake_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {route.module_snake_case}.{route.model_snake_case}.{instance_id}')
            
            server.log(f'PUT {route.module_snake_case}.{route.model_snake_case}/{instance_id}')
            raise JSONResponse('200 OK', model_to_json(updated_item))

        # delete #

        elif request.env['REQUEST_METHOD'] == 'DELETE':
            ack = db_model_delete(server, route.model_class, instance_id)
            server.log(f'DELETE {route.module_snake_case}.{route.model_snake_case}/{instance_id}')
            raise JSONResponse('204 No Content', ack)
        
        # invalid method #

        else:
            server.log(f'ERROR 405 {route.module_snake_case}.{route.model_snake_case}/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    #
    # model routes
    #

    elif re.match(route.api_model_regex, request.env['PATH_INFO']):

        # create #

        if request.env['REQUEST_METHOD'] == 'POST':
            incoming_item = route.model_class(**json.loads(request.raw_req_body.decode('utf-8')))
            item = db_model_create(server, route.model_class, incoming_item)

            server.log(f'POST {route.module_snake_case}.{route.model_snake_case} - id: {item.id}')
            raise JSONResponse('200 OK', model_to_json(item))
        
        # list #
        
        elif request.env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(request.env['QUERY_STRING'])
            offset = int(query.get('offset', [0])[0])
            limit = int(query.get('limit', [25])[0])

            items = db_model_list(server, route.model_class, offset=offset, limit=limit)
            server.log(f'GET {route.module_snake_case}.{route.model_snake_case}')

            result = ModelListResult(items=items, total=len(items))
            raise JSONResponse('200 OK', list_to_json(result))
        
        else:
            server.log(f'ERROR 405 {route.module_snake_case}.{route.model_snake_case}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
