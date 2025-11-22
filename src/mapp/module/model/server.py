import json
import re

from urllib.parse import parse_qs

from mapp.errors import NotFoundError, RequestError
from mapp.context import MappContext
from mapp.types import JSONResponse, model_to_json, list_to_json, ModelListResult
from mapp.module.model.db import *


__all__ = [
    'model_routes'
]


#
# router
#

def model_routes(ctx: MappContext, model_class:type, env:dict, raw_req_body:bytes):

    #
    # init
    #
    
    model_snake_case = model_class._model_spec['name']['snake_case']
    module_snake_case = model_class._model_spec['module']['snake_case']
    api_instance_regex = rf'/api/{module_snake_case}/{model_snake_case}/(.+)'
    api_model_regex = rf'/api/{module_snake_case}/{model_snake_case}'

    #
    # instance routes
    #

    if (instance := re.match(api_instance_regex, env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)

        # read #

        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_model_read(ctx, model_class, instance_id)
                ctx['log'](f'GET {module_snake_case}.{model_snake_case}/{instance_id}')
                raise JSONResponse('200 OK', model_to_json(item))
            
            except NotFoundError:
                ctx['log'](f'GET {module_snake_case}.{model_snake_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {module_snake_case}.{model_snake_case}.{instance_id}')

        # update #

        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_item = model_class(**json.loads(raw_req_body.decode('utf-8')))

            if instance_id != str(incoming_item.id):
                raise RequestError('400 Bad Request', f'{model_snake_case} id mismatch')
            try:
                updated_item = db_model_update(ctx, model_class, instance_id, incoming_item)
            except NotFoundError:
                ctx['log'](f'PUT {module_snake_case}.{model_snake_case}/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found {module_snake_case}.{model_snake_case}.{instance_id}')
            
            ctx['log'](f'PUT {module_snake_case}.{model_snake_case}/{instance_id}')
            raise JSONResponse('200 OK', model_to_json(updated_item))

        # delete #

        elif env['REQUEST_METHOD'] == 'DELETE':
            ack = db_model_delete(ctx, model_class, instance_id)
            ctx['log'](f'DELETE {module_snake_case}.{model_snake_case}/{instance_id}')
            raise JSONResponse('204 No Content', ack)
        
        # invalid method #

        else:
            ctx['log'](f'ERROR 405 {module_snake_case}.{model_snake_case}/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    #
    # model routes
    #

    elif re.match(api_model_regex, env['PATH_INFO']):

        # create #

        if env['REQUEST_METHOD'] == 'POST':
            incoming_item = model_class(**json.loads(raw_req_body.decode('utf-8')))
            item = db_model_create(ctx, model_class, incoming_item)

            ctx['log'](f'POST {module_snake_case}.{model_snake_case} - id: {item.id}')
            raise JSONResponse('200 OK', model_to_json(item))
        
        # list #
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = int(query.get('offset', [0])[0])
            limit = int(query.get('limit', [25])[0])

            items = db_model_list(ctx, model_class, offset=offset, limit=limit)
            ctx['log'](f'GET {module_snake_case}.{model_snake_case}')

            result = ModelListResult(items=items, total=len(items))
            raise JSONResponse('200 OK', list_to_json(result))
        
        else:
            ctx['log'](f'ERROR 405 {module_snake_case}.{model_snake_case}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')