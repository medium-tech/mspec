import re
from urllib.parse import parse_qs
from core.exceptions import NotFoundError, RequestError, JSONResponse
from template_module.single_model.model import SingleModel
from template_module.single_model.db import *

# vars :: {"template_module": "module.name.snake_case", "template-module": "module.name.kebab_case"}
# vars :: {"single_model": "model.name.snake_case", "single model": "model.name.lower_case"}
# vars :: {"single-model": "model.name.kebab_case", "SingleModel": "model.name.pascal_case"}

__all__ = [
    'single_model_routes'
]

#
# router
#

def single_model_routes(ctx:dict, env:dict, raw_req_body:bytes):

    # single model - instance routes #

    if (instance := re.match(r'/api/template-module/single-model/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_single_model(ctx, instance_id)
                ctx['log'](f'GET template-module.single-model/{instance_id}')
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET template-module.single-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found template-module.single-model.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_item = SingleModel.from_json(raw_req_body.decode('utf-8'))

            try:
                if instance_id != incoming_item.id:
                    raise RequestError('400 Bad Request', 'single model id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'single model is missing id')

            try:
                updated_item = db_update_single_model(ctx, incoming_item)
            except NotFoundError:
                ctx['log'](f'PUT template-module.single-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found template-module.single-model.{instance_id}')
            
            ctx['log'](f'PUT template-module.single-model/{instance_id}')
            raise JSONResponse('200 OK', updated_item.to_dict())

        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_single_model(ctx, instance_id)
            ctx['log'](f'DELETE template-module.single-model/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 template-module.single-model/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # single model - model routes #

    elif re.match(r'/api/template-module/single-model', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            incoming_item = SingleModel.from_json(raw_req_body.decode('utf-8'))
            item = db_create_single_model(ctx, incoming_item)

            ctx['log'](f'POST template-module.single-model - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_single_model(ctx, offset=int(offset), limit=int(limit))
            ctx['log'](f'GET template-module.single-model')

            raise JSONResponse('200 OK', [SingleModel.to_dict(item) for item in items])
    
        else:
            ctx['log'](f'ERROR 405 template-module.single-model')
            raise RequestError('405 Method Not Allowed', 'invalid request method')