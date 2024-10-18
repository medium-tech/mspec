import re
from urllib.parse import parse_qs
from sample.sample_item import sample_item_from_json
from sample.sample_item.db import *

from core.exceptions import NotFoundError, RequestError, JSONResponse

# vars :: {"sample": "module.name.snake_case", "sample_item": "model.name.snake_case", "sample item": "model.name.lower_case", "sample-item": "model.name.kebab_case"}

__all__ = [
    'sample_item_routes'
]

#
# router
#

def sample_item_routes(ctx:dict, env:dict):

    # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    req_body_raw:bytes = env['wsgi.input'].read()
    # but we'll only decode and parse it if needed
    req_body = lambda: sample_item_from_json(req_body_raw.decode('utf-8'))

    # sample item - instance routes #

    if (instance := re.match(r'/api/sample/sample-item/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            # uwsgi.log(f'ROUTE - GET sample.sample_item/{instance_id}')

            try:
                item = db_read_sample_item(ctx, instance_id)
                # uwsgi.log(f'ROUTE - GET sample.sample_item/{instance_id} - found: {item is not None}')
                raise JSONResponse('200 OK', item)
            except NotFoundError:
                raise RequestError('404 Not Found', f'not found sample.sample_item.{instance_id}')

        elif env['REQUEST_METHOD'] == 'PUT':
            # uwsgi.log(f'ROUTE - PUT sample.sample_item/{instance_id}')
            db_update_sample_item(ctx, instance_id, req_body())
            raise JSONResponse('204 No Content')

        elif env['REQUEST_METHOD'] == 'DELETE':
            # uwsgi.log(f'ROUTE - DELETE sample.sample_item/{instance_id}')
            db_delete_sample_item(ctx, instance_id)
            raise JSONResponse('204 No Content')
        
        else:
            # uwsgi.log(f'ROUTE - ERROR 405 sample.sample_item/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

    # sample item - model routes #

    elif re.match(r'/api/sample/sample-item', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            # uwsgi.log(f'ROUTE - POST sample.sample_item')
            result_id = db_create_sample_item(ctx, req_body())
            raise JSONResponse('200 OK', {'id': result_id})
        
        elif env['REQUEST_METHOD'] == 'GET':
            # uwsgi.log(f'ROUTE - GET sample.sample_item')
    
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_sample_item(ctx, offset=int(offset), limit=int(limit))
            raise JSONResponse('200 OK', {'items': items})
    
        else:
            # uwsgi.log(f'ROUTE - ERROR 405 sample.sample_item')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
