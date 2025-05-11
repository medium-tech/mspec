import re
from urllib.parse import parse_qs
from test_module.test_model.model import TestModel
from test_module.test_model.db import *

from core.exceptions import NotFoundError, RequestError, JSONResponse

# vars :: {"test_module": "module.name.snake_case", "test-module": "module.name.kebab_case"}
# vars :: {"test_model": "model.name.snake_case", "test model": "model.name.lower_case"}
# vars :: {"test-model": "model.name.kebab_case", "TestModel": "model.name.pascal_case"}

__all__ = [
    'test_model_routes'
]

#
# router
#

def test_model_routes(ctx:dict, env:dict, raw_req_body:bytes):

    # test model - instance routes #

    if (instance := re.match(r'/api/test-module/test-model/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_test_model(ctx, instance_id)
                ctx['log'](f'GET test-module.test-model/{instance_id}')
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET test-module.test-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found test-module.test-model.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_item = TestModel.from_json(raw_req_body.decode('utf-8'))

            try:
                if instance_id != incoming_item.id:
                    raise RequestError('400 Bad Request', 'test model id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'test model is missing id')

            try:
                updated_item = db_update_test_model(ctx, incoming_item)
            except NotFoundError:
                ctx['log'](f'PUT test-module.test-model/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found test-module.test-model.{instance_id}')
            
            ctx['log'](f'PUT test-module.test-model/{instance_id}')
            raise JSONResponse('200 OK', updated_item.to_dict())

        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_test_model(ctx, instance_id)
            ctx['log'](f'DELETE test-module.test-model/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 test-module.test-model/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # test model - model routes #

    elif re.match(r'/api/test-module/test-model', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            incoming_item = TestModel.from_json(raw_req_body.decode('utf-8'))
            item = db_create_test_model(ctx, incoming_item)

            ctx['log'](f'POST test-module.test-model - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_test_model(ctx, offset=int(offset), limit=int(limit))
            ctx['log'](f'GET test-module.test-model')

            raise JSONResponse('200 OK', [TestModel.to_dict(item) for item in items])
    
        else:
            ctx['log'](f'ERROR 405 test-module.test-model')
            raise RequestError('405 Method Not Allowed', 'invalid request method')