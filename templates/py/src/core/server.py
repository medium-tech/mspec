import json
import re
import os

from traceback import format_exc
from urllib.parse import parse_qs

from core.models import *
from core.db import *
from core.exceptions import RequestError, JSONResponse, NotFoundError
# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case"}
from sample_module import sample_module_routes
# end for ::

import uwsgi
from uwsgidecorators import postfork

#
# routes
#

def user_routes(ctx:dict, env:dict, raw_req_body:bytes):
    
    # user - instance routes #

    if (instance := re.match(r'/api/core/user/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_user(ctx, instance_id)
                ctx['log'](f'GET core.user/{instance_id}')
                raise JSONResponse('200 OK', item)
            except NotFoundError:
                ctx['log'](f'GET core.user/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.user.{instance_id}')
        
        elif env['REQUEST_METHOD'] == 'PUT':
            req_body = user_from_json(raw_req_body.decode('utf-8'))
            try:
                if instance_id != req_body['id']:
                    raise RequestError('400 Bad Request', 'user id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'user is missing id')
            
            try:
                db_update_user(ctx, req_body)
            except NotFoundError:
                ctx['log'](f'PUT core.user/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.user.{instance_id}')
            
            ctx['log'](f'PUT core.user/{instance_id}')
            raise JSONResponse('204 No Content')
        
        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_user(ctx, instance_id)
            ctx['log'](f'DELETE core.user/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 core.user/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
        
    # user - model routes #

    elif re.match(r'/api/core/user', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            req_body = user_from_json(raw_req_body.decode('utf-8'))
            item = db_create_user(ctx, req_body)
            ctx['log'](f'POST core.user - id: {item["id"]} {item}')
            raise JSONResponse('200 OK', item)
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [10])[0]

            items = db_list_user(ctx, int(offset), int(limit))
            ctx['log'](f'GET core.user')

            raise JSONResponse('200 OK', items)
        
        else:
            ctx['log'](f'ERROR 405 core.user')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

def profile_routes(ctx:dict, env:dict, raw_req_body:bytes):

    # profile - instance routes #

    if (instance := re.match(r'/api/core/profile/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_profile(ctx, instance_id)
                ctx['log'](f'GET core.profile/{instance_id}')
                raise JSONResponse('200 OK', item)
            except NotFoundError:
                ctx['log'](f'GET core.profile/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.profile.{instance_id}')
        
        elif env['REQUEST_METHOD'] == 'PUT':
            req_body = profile_from_json(raw_req_body.decode('utf-8'))

            try:
                if instance_id != req_body['id']:
                    raise RequestError('400 Bad Request', 'user id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'user is missing id')
            
            try:
                db_update_profile(ctx, req_body)
            except NotFoundError:
                ctx['log'](f'PUT core.profile/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.profile.{instance_id}')
            
            ctx['log'](f'PUT core.profile/{instance_id}')
            raise JSONResponse('204 No Content')
        
        elif env['REQUEST_METHOD'] == 'DELETE':
            db_delete_profile(ctx, instance_id)
            ctx['log'](f'DELETE core.profile/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 core.profile/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
        
    # profile - model routes #

    elif re.match(r'/api/core/profile', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            req_body = profile_from_json(raw_req_body.decode('utf-8'))
            item = db_create_profile(ctx, req_body)
            ctx['log'](f'POST core.profile - id: {item["id"]}')
            raise JSONResponse('200 OK', item)
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [10])[0]

            items = db_list_profile(ctx, int(offset), int(limit))
            ctx['log'](f'GET core.profile')

            raise JSONResponse('200 OK', items)
        
        else:
            ctx['log'](f'ERROR 405 core.profile')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

#
# app
#

route_list = [
    user_routes,
    profile_routes
]

# for :: {% for module in modules.values() %} :: {"sample_module": "module.name.snake_case"}
route_list.extend(sample_module_routes)
# end for ::

server_ctx = {
    'log': uwsgi.log
}

@postfork
def initialize():
    global server_ctx
    server_ctx.update(create_db_context())
    uwsgi.log(f'INITIALIZED - pid: {os.getpid()}')

def application(env, start_response):

    # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    req_body:bytes = env['wsgi.input'].read()
    env['wsgi.input'].close()

    for route in route_list:
        try:
            route(server_ctx, env, req_body)
        except RequestError as e:
            body = {'error': e.msg}
            status_code = e.status
            break

        except JSONResponse as e:
            body = e.data
            status_code = e.status
            break

        except Exception as e:
            body = {'error': 'internal server error'}
            status_code = '500 Internal Server Error'
            uwsgi.log(f'ERROR - {e.__class__.__name__} - {e} \n' + format_exc())
            break
    else:
        body = {'error': f'not found: ' + env['PATH_INFO']}
        status_code = '404 Not Found'
    
    start_response(status_code, [('Content-Type','application/json')])

    uwsgi.log(f'RESPONSE - {status_code}')
    return [json.dumps(body).encode('utf-8')]
