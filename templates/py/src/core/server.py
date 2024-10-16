import json
from os import getpid
from traceback import format_exc
from core.db import create_db_context
from core.exceptions import RequestError, JSONResponse
# for :: {% for module in project.modules %} :: {"sample": "module.snake_case"}
from sample import sample_routes
# end for ::

import uwsgi
from uwsgidecorators import postfork

route_list = []
# for :: {% for module in project.modules %} :: {"sample": "module.snake_case"}
route_list.extend(sample_routes)
# end for ::


server_ctx = {}

#
# entry point
#

@postfork
def initialize():
    global server_ctx
    server_ctx.update(create_db_context())
    uwsgi.log(f'INITIALIZED - pid: {getpid()}')

def application(env, start_response):

    for route in route_list:
        try:
            route(server_ctx, env)
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
