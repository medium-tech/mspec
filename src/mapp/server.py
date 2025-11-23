import os
import time
import uwsgi
from traceback import format_exc

from mapp.context import get_context_from_env, MappContext, RequestContext, RouteContext
from mapp.errors import *
from mapp.types import JSONResponse, PlainTextResponse, to_json


def debug_routes(route: RouteContext, server: MappContext, request: RequestContext):
    column_width = 42

    output = 'Debug Info\n\n'

    output += 'MappContext:\n'
    output += f'MappContext.server_port ::{server.server_port:<{column_width}}\n'
    output += f'MappContext.client_host ::{server.client_host:<{column_width}}\n'
    output += f'MappContext.log ::{type(server.log)=:<{column_width}}\n\n'
    output += f'MappContext.db ::{type(server.db)=:<{column_width}}\n'
    output += f' :: DBContext.db_url ::{server.db.db_url:<{column_width}}\n'
    output += f' :: DBContext.connection ::{type(server.db.connection)=:<{column_width}}\n'
    output += f' :: DBContext.cursor ::{type(server.db.cursor)=:<{column_width}}\n'
    output += f' :: DBContext.commit ::{type(server.db.commit)=:<{column_width}}\n\n'

    output += f'RequestContext.raw_req_body ::{request.raw_req_body:<{column_width}} {type(request.raw_req_body)=} {len(request.raw_req_body)=}\n'
    output += 'RequestContext.env ::\n\n'
    for key in request.env:
        output += f' :: {key:<{column_width}}:: {request.env[key]}\n'
    output += '\n'

    debug_delay = os.environ.get('DEBUG_DELAY', None)
    output += f'DEBUG_DELAY :: {debug_delay}\n\n'

    output += f'RouteContext :: {route}\n'
    output += ' :: unused in debug_routes\n'

    raise PlainTextResponse('200 OK', output)


server_ctx = get_context_from_env()
server_ctx.log = uwsgi.log

route_list = [debug_routes]


def application(env, start_response):

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
