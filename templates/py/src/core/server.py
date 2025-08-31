import re
import os
import time

from copy import deepcopy
from traceback import format_exc
from urllib.parse import parse_qs

from core.auth import create_new_user, login_user, get_user_id_from_token
from core.types import to_json
from core.models import *
from core.db import *
from core.exceptions import RequestError, JSONResponse, PlainTextResponse, NotFoundError, AuthenticationError, ForbiddenError
# for :: {% for item in all_models %} :: {"template_module": "item.module.name.snake_case", "single_model": "item.model.name.snake_case"}
from template_module.single_model.server import single_model_routes
# end for ::

# ignore ::
from template_module.multi_model.server import multi_model_routes
# end ignore ::

import uwsgi
from uwsgidecorators import postfork

#
# routes
#

def debug_routes(ctx:dict, env:dict, raw_req_body:bytes):
    output = ''
    keys = sorted(env.keys())
    longest_key_len = max(len(key) for key in keys)
    for key in keys:
        output += f'{key:<{longest_key_len}}: {env[key]}\n'

    debug_delay = os.environ.get('DEBUG_DELAY', None)
    output += f'\nDEBUG_DELAY: {debug_delay}\n'
    raise PlainTextResponse('200 OK', output)

def auth_routes(ctx:dict, env:dict, raw_req_body:bytes):
    if re.match(r'/api/auth/login', env['PATH_INFO']):
        
        if env['REQUEST_METHOD'] == 'POST':
            form_data = parse_qs(raw_req_body.decode('utf-8'), strict_parsing=True)
            ctx['log'](f'POST core.auth.login')
            token = login_user(ctx, form_data['email'][0], form_data['password'][0])
            raise JSONResponse('200 OK', token.to_dict())
        
        else:
            ctx['log'](f'ERROR 405 core.auth.login')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

def user_routes(ctx:dict, env:dict, raw_req_body:bytes):
    
    # user - instance routes #

    if (instance := re.match(r'/api/core/user/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        cur_user:User = ctx['auth']['get_user']()

        if cur_user.id != instance_id:
            raise ForbiddenError('Resource is not accessible')
        
        if env['REQUEST_METHOD'] == 'GET':
            try:
                item = db_read_user(ctx, instance_id)
                ctx['log'](f'GET core.user/{instance_id}')
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET core.user/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.user.{instance_id}')
        
        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_user = User.from_json(raw_req_body.decode('utf-8'))
            try:
                if instance_id != incoming_user.id:
                    raise RequestError('400 Bad Request', 'user id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'user is missing id')
            
            try:
                updated_user = db_update_user(ctx, incoming_user)
            except NotFoundError:
                ctx['log'](f'PUT core.user/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.user.{instance_id}')
            
            ctx['log'](f'PUT core.user/{instance_id}')
            raise JSONResponse('200 Ok', updated_user.to_dict())
        
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
            incoming_user = CreateUser.from_json(raw_req_body.decode('utf-8'))
            ctx['log'](f'POST core.user - {type(incoming_user)} {incoming_user}')
            item = create_new_user(ctx, incoming_user)
            ctx['log'](f'POST core.user - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            raise ForbiddenError('Resource is not accessible')
        
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
                raise JSONResponse('200 OK', item.to_dict())
            except NotFoundError:
                ctx['log'](f'GET core.profile/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.profile.{instance_id}')
        
        elif env['REQUEST_METHOD'] == 'PUT':
            incoming_profile = Profile.from_json(raw_req_body.decode('utf-8'))

            cur_user:User = ctx['auth']['get_user']()
            if incoming_profile.user_id != cur_user.id:
                raise ForbiddenError('Resource is not accessible')

            try:
                if instance_id != incoming_profile.id:
                    raise RequestError('400 Bad Request', 'user id mismatch')
            except KeyError:
                raise RequestError('400 Bad Request', 'user is missing id')
            
            try:
                updated_profile = db_update_profile(ctx, incoming_profile)
            except NotFoundError:
                ctx['log'](f'PUT core.profile/{instance_id} - Not Found')
                raise RequestError('404 Not Found', f'not found core.profile.{instance_id}')
            
            ctx['log'](f'PUT core.profile/{instance_id}')
            raise JSONResponse('200 Ok', updated_profile.to_dict())
        
        elif env['REQUEST_METHOD'] == 'DELETE':
            cur_user:User = ctx['auth']['get_user']()
            if incoming_profile.user_id != cur_user.id:
                raise ForbiddenError('Resource is not accessible')
            
            db_delete_profile(ctx, instance_id)
            ctx['log'](f'DELETE core.profile/{instance_id}')
            raise JSONResponse('204 No Content')
        
        else:
            ctx['log'](f'ERROR 405 core.profile/{instance_id}')
            raise RequestError('405 Method Not Allowed', 'invalid request method')
        
    # profile - model routes #

    elif re.match(r'/api/core/profile', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            cur_user:User = ctx['auth']['get_user']()

            incoming_profile = Profile.from_json(raw_req_body.decode('utf-8'))
            if incoming_profile.user_id != cur_user.id:
                raise ForbiddenError('Resource is not accessible')
            
            item = db_create_profile(ctx, incoming_profile)

            ctx['log'](f'POST core.profile - id: {item.id}')
            raise JSONResponse('200 OK', item.to_dict())
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            offset = query.get('offset', [0])[0]
            limit = query.get('limit', [25])[0]

            items = db_list_profile(ctx, int(offset), int(limit))
            ctx['log'](f'GET core.profile')

            raise JSONResponse('200 OK', [Profile.to_dict(item) for item in items])
        
        else:
            ctx['log'](f'ERROR 405 core.profile')
            raise RequestError('405 Method Not Allowed', 'invalid request method')

#
# app
#

route_list = [
    auth_routes,
    user_routes,
    profile_routes,
    # for :: {% for item in all_models %} :: {"single_model": "item.model.name.snake_case"}
    single_model_routes,
    # end for ::
    # ignore ::
    multi_model_routes,
    debug_routes
    # end ignore ::
]

server_ctx = {
    'log': uwsgi.log
}

@postfork
def initialize():
    global server_ctx
    server_ctx.update(create_db_context())
    create_db_tables(server_ctx)
    uwsgi.log(f'INITIALIZED - pid: {os.getpid()}')

def get_user_id(env:dict) -> User:
    """
    return user id as string for logged in user from HTTP Authorization header
    raise AuthenticationError if not logged in or invalid header
    """
    global server_ctx
    try:
        auth_header = env['HTTP_AUTHORIZATION']
    except KeyError:
        raise AuthenticationError('Not logged in')
    
    return get_user_id_from_token(server_ctx, auth_header[7:])

def get_user(env:dict) -> User:
    """
    get user id for logged in user from HTTP Authorization header,
        and then get user object from database
    raise AuthenticationError if not logged in or invalid header
    """
    user_id = get_user_id(env)
    try:
        return db_read_user(server_ctx, user_id)
    except NotFoundError:
        raise AuthenticationError('Could not validate credentials')

def application(env, start_response):

    # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    req_body:bytes = env['wsgi.input'].read()
    env['wsgi.input'].close()

    request_context = deepcopy(server_ctx)

    assert 'auth' not in server_ctx
    assert 'auth' not in request_context
   
    request_context['auth'] = {
        'get_user_id': lambda: get_user_id(env),
        'get_user': lambda: get_user(env)
    }

    try:
        debug_delay = float(os.environ['DEBUG_DELAY'])
        time.sleep(debug_delay)
    except KeyError:
        pass

    for route in route_list:
        try:
            route(request_context, env, req_body)

        except AuthenticationError as e:
            body = {'error': 'Unauthorized'}
            status_code = '401 Unauthorized'
            content_type = JSONResponse.content_type
            break

        except ForbiddenError as e:
            body = {'error': 'Forbidden'}
            status_code = '403 Forbidden'
            content_type = JSONResponse.content_type
            break

        except RequestError as e:
            body = {'error': e.msg}
            status_code = e.status
            content_type = JSONResponse.content_type 
            break

        except PlainTextResponse as e:
            body = e.text
            status_code = e.status
            content_type = e.content_type
            break

        except JSONResponse as e:
            body = e.data
            status_code = e.status
            content_type = e.content_type
            break

        except Exception as e:
            body = {'error': 'internal server error'}
            status_code = '500 Internal Server Error'
            content_type = JSONResponse.content_type
            uwsgi.log(f'ERROR - {e.__class__.__name__} - {e} \n' + format_exc())
            break
        
    else:
        body = {'error': f'not found: ' + env['PATH_INFO']}
        status_code = '404 Not Found'
        content_type = JSONResponse.content_type

    start_response(status_code, [('Content-Type', content_type)])

    uwsgi.log(f'RESPONSE - {status_code}')
    if content_type == JSONResponse.content_type:
        return [to_json(body).encode('utf-8')]
    else:
        return [body.encode('utf-8')]
