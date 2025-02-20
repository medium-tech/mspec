import re
from urllib.parse import parse_qs
from sample_module.example_item.model import ExampleItem
from sample_module.example_item.db import *

from core.exceptions import NotFoundError, RequestError, JSONResponse

# vars :: {"sample_module": "module.name.snake_case", "sample-module": "module.name.kebab_case"}
# vars :: {"example_item": "model.name.snake_case", "example item": "model.name.lower_case", "example-item": "model.name.kebab_case"}

__all__ = [
    'example_item_routes'
]

#
# router
#

def example_item_routes(ctx:dict, env:dict, raw_req_body:bytes):

    # example item - instance routes #

    if (instance := re.match(r'/api/sample-module/example-item/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_example_item(ctx, instance_id)
                ctx['log'](f'GET sample-module.example-item/{instance_id}')
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET sample-module.example-item/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found sample-module.example-item.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_item = ExampleItem.from_json(raw_req_body.decode('utf-8'))

            try:
                if instance_id != incoming_item.id:
                    raise RequestError('400 Bad Request', 'example item id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'example item is missing id')

            try:
                updated_item = db_update_example_item(ctx, incoming_item)
            except NotFoundError:
                ctx['log'](f'PUT sample-module.example-item/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found sample-module.example-item.{instance_id}')
            
            ctx['log'](f'PUT sample-module.example-item/{instance_id}')
            raise JSONResponse('200 OK', updated_item.to_dict())

        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_example_item(ctx, instance_id)
            ctx['log'](f'DELETE sample-module.example-item/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 sample-module.example-item/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # example item - model routes #

    elif re.match(r'/api/sample-module/example-item', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            incoming_item = ExampleItem.from_json(raw_req_body.decode('utf-8'))
            item = db_create_example_item(ctx, incoming_item)

            ctx['log'](f'POST sample-module.example-item - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_example_item(ctx, offset=int(offset), limit=int(limit))
            ctx['log'](f'GET sample-module.example-item')

            raise JSONResponse('200 OK', [ExampleItem.to_dict(item) for item in items])
    
        else:
            ctx['log'](f'ERROR 405 sample-module.example-item')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
