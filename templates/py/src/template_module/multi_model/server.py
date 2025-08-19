import json
import re
from urllib.parse import parse_qs
from core.exceptions import NotFoundError, RequestError, JSONResponse
from template_module.multi_model.model import MultiModel
from template_module.multi_model.db import *

__all__ = [
    'multi_model_routes'
]

#
# router
#

def multi_model_routes(ctx:dict, env:dict, raw_req_body:bytes):

    # multi model - instance routes #

    if (instance := re.match(r'/api/template-module/multi-model/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_multi_model(ctx, instance_id)
                ctx['log'](f'GET template-module.multi-model/{instance_id}')
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET template-module.multi-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found template-module.multi-model.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_item = MultiModel(**json.loads(raw_req_body.decode('utf-8'))).convert_types()

            try:
                if instance_id != incoming_item.id:
                    raise RequestError('400 Bad Request', 'multi model id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'multi model is missing id')

            try:
                updated_item = db_update_multi_model(ctx, incoming_item)
            except NotFoundError:
                ctx['log'](f'PUT template-module.multi-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found template-module.multi-model.{instance_id}')

            ctx['log'](f'PUT template-module.multi-model/{instance_id}')
            raise JSONResponse('200 OK', updated_item.to_dict())

        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_multi_model(ctx, instance_id)
            ctx['log'](f'DELETE template-module.multi-model/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 template-module.multi-model/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # multi model - model routes #

    elif re.match(r'/api/template-module/multi-model', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            incoming_item = MultiModel(**json.loads(raw_req_body.decode('utf-8'))).convert_types()
            item = db_create_multi_model(ctx, incoming_item)

            ctx['log'](f'POST template-module.multi-model - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_multi_model(ctx, offset=int(offset), limit=int(limit))
            ctx['log'](f'GET template-module.multi-model')

            raise JSONResponse('200 OK', [MultiModel.to_dict(item) for item in items])

        else:
            ctx['log'](f'ERROR 405 template-module.multi-model')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
