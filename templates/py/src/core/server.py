import json
from os import getpid
from traceback import format_exc
from core.db import db_init
from sample.sample_item.server import sample_item_routes
from core.exceptions import RequestError, JSONResponse
from sample.db import *

import uwsgi
from uwsgidecorators import postfork

route_list = [
    sample_item_routes
]

#
# entry point
#

@postfork
def initialize():
    db_init()
    uwsgi.log(f'INITIALIZED - pid: {getpid()}')

def application(env, start_response):

    for route in route_list:
        try:
            route(env)
        except RequestError as e:
            body = {'error': e.msg}
            status_code = e.status

        except JSONResponse as e:
            body = e.data
            status_code = e.status

        except Exception as e:
            body = {'error': 'internal server error'}
            status_code = '500 Internal Server Error'
            uwsgi.log(f'ERROR - {e.__class__.__name__} - {e} \n' + format_exc())
    else:
        body = {'error': f'not found: ' + env['PATH_INFO']}
        status_code = '404 Not Found'
    
    start_response(status_code, [('Content-Type','application/json')])

    uwsgi.log(f'RESPONSE - {status_code}')
    return [json.dumps(body).encode('utf-8')]
