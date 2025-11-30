import os
import re
import time
import uwsgi

from traceback import format_exc

from mapp.context import get_context_from_env, MappContext, RequestContext, spec_from_env
from mapp.errors import *
from mapp.types import JSONResponse, PlainTextResponse, to_json
from mapp.module.model.db import db_model_create_table
from mapp.module.model.server import create_model_routes


def debug_routes(server: MappContext, request: RequestContext):
    if re.match('/api/debug', request.env['PATH_INFO']) is None:
        return
    
    main_col = 30
    header_col = 42

    output = 'Debug Info\n\n'

    output += 'MappContext:\n'
    output += f' :: {"MappContext.server_port": <{main_col}}:: {server.server_port}\n'
    output += f' :: {"MappContext.client_host": <{main_col}}:: {server.client_host}\n'
    output += f' :: {"MappContext.log": <{main_col}}:: {str(type(server.log))}\n\n'
    output += f' :: {"MappContext.db": <{main_col}}:: {str(type(server.db))}\n'
    output += f'   :: {"DBContext.db_url": <{header_col}}:: {str(server.db.db_url)}\n'
    output += f'   :: {"DBContext.connection": <{header_col}}:: {str(type(server.db.connection))}\n'
    output += f'   :: {"DBContext.cursor": <{header_col}}:: {str(type(server.db.cursor))}\n'
    output += f'   :: {"DBContext.commit": <{header_col}}:: {str(type(server.db.commit))}\n\n'
    output += f'RequestContext.raw_req_body ::{str(type(request.raw_req_body))} {len(request.raw_req_body)=}\n'
    output += 'RequestContext.env ::\n\n'
    for key in request.env:
        output += f' :: {key:<{header_col}}:: {request.env[key]}\n'
    output += '\n'

    debug_delay = os.environ.get('DEBUG_DELAY', None)
    output += f'DEBUG_DELAY :: {debug_delay}\n\n'

    raise PlainTextResponse('200 OK', output)


server_ctx = get_context_from_env()
server_ctx.log = uwsgi.log

route_list = []

spec = spec_from_env()

try:
    spec_modules = spec['modules']
except KeyError:
    raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

for module in spec_modules.values():
    if module.get('hidden', False) is True:
        continue

    try:
        spec_models = module['models']
    except KeyError:
        raise MappError('NO_MODELS_DEFINED', f'No models defined in module: {module["name"]["kebab_case"]}')

    for model in spec_models.values():
        if model.get('hidden', False) is True:
            continue

        route_resolver, model_class = create_model_routes(module, model)
        route_list.append(route_resolver)
        db_model_create_table(server_ctx, model_class)

route_list.append(debug_routes)

def application(env, start_response):

    server_ctx.log(f'REQUEST - {env["REQUEST_METHOD"]} {env["PATH_INFO"]}')

    request = RequestContext(
        env=env,
        # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
        raw_req_body=env['wsgi.input'].read()
    )
   
    request.env['wsgi.input'].close()

    try:
        debug_delay = float(os.environ['DEBUG_DELAY'])
        time.sleep(debug_delay)
    except KeyError:
        pass

    for route in route_list:
        try:
            route(server_ctx, request)

        # success responses #

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

        # error responses #

        except NotFoundError as e:
            # for when a model is not found
            body = e.to_dict()
            status_code = '404 Not Found'
            content_type = JSONResponse.content_type
            break

        except AuthenticationError as e:
            body = {'code': 'UNAUTHORIZED', 'message': str(e)}
            status_code = '401 Unauthorized'
            content_type = JSONResponse.content_type
            break

        except ForbiddenError as e:
            body = {'code': 'FORBIDDEN', 'message': str(e)}
            status_code = '403 Forbidden'
            content_type = JSONResponse.content_type
            break

        except MappValidationError as e:
            body = e.to_dict()
            status_code = '400 Bad Request'
            content_type = JSONResponse.content_type
            break

        except RequestError as e:
            body = e.to_dict()
            status_code = e.status
            content_type = JSONResponse.content_type 
            break

        # uncaught exception | internal server error #

        except Exception as e:
            body = {'code': 'INTERNAL_SERVER_ERROR', 'message': str(e)}
            status_code = '500 Internal Server Error'
            content_type = JSONResponse.content_type
            server_ctx.log(f'ERROR - {e.__class__.__name__} - {e} \n' + format_exc())
            break

    # url not found #
        
    else:
        # for when a route is not found
        body = {'code': 'NOT_FOUND', 'message': f'not found: ' + env['PATH_INFO']}
        status_code = '404 Not Found'
        content_type = JSONResponse.content_type

    start_response(status_code, [('Content-Type', content_type)])

    server_ctx.log(f'RESPONSE - {status_code} - {env["REQUEST_METHOD"]} {env["PATH_INFO"]}')
    if content_type == JSONResponse.content_type:
        return [to_json(body).encode('utf-8')]
    else:
        return [body.encode('utf-8')]
