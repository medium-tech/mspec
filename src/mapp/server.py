import os
import time
import uwsgi
from traceback import format_exc

from mapp.context import get_context_from_env, MappContext
from mapp.errors import *
from mapp.types import JSONResponse, PlainTextResponse, to_json

def debug_routes(ctx: MappContext, env:dict, raw_req_body:bytes):
    output = ''
    keys = sorted(env.keys())
    longest_key_len = max(len(key) for key in keys)
    for key in keys:
        output += f'{key:<{longest_key_len}}: {env[key]}\n'

    debug_delay = os.environ.get('DEBUG_DELAY', None)
    output += f'\nDEBUG_DELAY: {debug_delay}\n'
    raise PlainTextResponse('200 OK', output)


server_ctx = get_context_from_env()
server_ctx.log = uwsgi.log

route_list = [debug_routes]


def application(env, start_response):

    # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
    req_body:bytes = env['wsgi.input'].read()
    env['wsgi.input'].close()

    try:
        debug_delay = float(os.environ['DEBUG_DELAY'])
        time.sleep(debug_delay)
    except KeyError:
        pass

    for route in route_list:
        try:
            route(request_context, env, req_body)

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
            body = {'code': 'NOT_FOUND', 'message': str(e)}
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

        except RequestError as e:
            body = {'code': 'REQUEST_ERROR', 'message': e.msg}
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

    server_ctx.log(f'RESPONSE - {status_code}')
    if content_type == JSONResponse.content_type:
        return [to_json(body).encode('utf-8')]
    else:
        return [body.encode('utf-8')]
