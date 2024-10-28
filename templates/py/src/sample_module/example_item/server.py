import re
from urllib.parse import parse_qs
from sample_module.example_item import example_item_from_json
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

def example_item_routes(ctx:dict, env:dict):

    # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    req_body_raw:bytes = env['wsgi.input'].read()
    # but we'll only decode and parse it if needed
    req_body = lambda: example_item_from_json(req_body_raw.decode('utf-8'))

    # example item - instance routes #

    if (instance := re.match(r'/api/sample-module/example-item/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            # uwsgi.log(f'ROUTE - GET sample-module.example-item/{instance_id}')

            try:
                item = db_read_example_item(ctx, instance_id)
                # uwsgi.log(f'ROUTE - GET sample-module.example-item/{instance_id} - found: {item is not None}')
                raise JSONResponse('200 OK', item)
            except NotFoundError:
                raise RequestError('404 Not Found', f'not found sample-module.example-item.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            # uwsgi.log(f'ROUTE - PUT sample-module.example-item/{instance_id}')
            db_update_example_item(ctx, instance_id, req_body())
            raise JSONResponse('204 No Content')

        elif env['REQUEST_METHOD'] == 'DELETE':
            # uwsgi.log(f'ROUTE - DELETE sample-module.example-item/{instance_id}')
            db_delete_example_item(ctx, instance_id)
            raise JSONResponse('204 No Content')
        
        else:
            # uwsgi.log(f'ROUTE - ERROR 405 sample-module.example-item/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # example item - model routes #

    elif re.match(r'/api/sample-module/example-item', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            # uwsgi.log(f'ROUTE - POST sample-module.example-item')
            result_id = db_create_example_item(ctx, req_body())
            raise JSONResponse('200 OK', {'id': result_id})
        
        elif env['REQUEST_METHOD'] == 'GET':
            # uwsgi.log(f'ROUTE - GET sample-module.example-item')
    
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_example_item(ctx, offset=int(offset), limit=int(limit))
            raise JSONResponse('200 OK', {'items': items})
    
        else:
            # uwsgi.log(f'ROUTE - ERROR 405 sample-module.example-item')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
