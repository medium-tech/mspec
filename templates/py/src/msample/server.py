import re
import json
from urllib.parse import parse_qs

from msample import from_json
from msample.db import *

__all__ = ['routes']

def dump_env(env):
    """
    REQUEST_METHOD :: GET
    PATH_INFO :: /my/url
    REQUEST_URI :: /my/url?arg1=hello&arg2=stuff
    QUERY_STRING :: arg1=hello&arg2=stuff
    SERVER_PROTOCOL :: HTTP/1.1
    SCRIPT_NAME :: 
    SERVER_NAME :: Brads-MBP-2
    SERVER_PORT :: 9090
    UWSGI_ROUTER :: http
    REMOTE_ADDR :: 127.0.0.1
    REMOTE_PORT :: 18884
    HTTP_HOST :: localhost:9090
    HTTP_SEC_FETCH_SITE :: none
    HTTP_CONNECTION :: keep-alive
    HTTP_UPGRADE_INSECURE_REQUESTS :: 1
    HTTP_SEC_FETCH_MODE :: navigate
    HTTP_ACCEPT :: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
    HTTP_USER_AGENT :: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15
    HTTP_ACCEPT_LANGUAGE :: en-US,en;q=0.9
    HTTP_SEC_FETCH_DEST :: document
    HTTP_ACCEPT_ENCODING :: gzip, deflate
    wsgi.input :: <uwsgi._Input object at 0x10020f6d0>
    wsgi.file_wrapper :: <built-in function uwsgi_sendfile>
    wsgi.version :: (1, 0)
    wsgi.errors :: <_io.TextIOWrapper name=2 mode='w' encoding='UTF-8'>
    wsgi.run_once :: False
    wsgi.multithread :: False
    wsgi.multiprocess :: False
    wsgi.url_scheme :: http
    uwsgi.version :: b'2.0.27'
    uwsgi.node :: b'Brads-MBP-2'
    """
    for key in env:
        print(f'{key} :: {env[key]}')


class RequestError(Exception):
    def __init__(self, msg:str, status:str) -> None:
        super().__init__(msg)
        self.msg = msg
        self.status = status

#
# router
#

def routes(env:dict):

    input_model = lambda: from_json(env['wsgi.input'].read().decode('utf-8'))

    # instance routes #

    if (instance := re.match(r'/api/sample/sample-item/(.+)', env['PATH_INFO'])) is not None:
        instance_id = instance.group(1)
        if env['REQUEST_METHOD'] == 'GET':
            if(item := db_read_sample_item(instance_id) is not None):
                return item
            else:
                raise RequestError('item not found', '404 Not Found')

        elif env['REQUEST_METHOD'] == 'PUT':
            return db_update_sample_item(instance_id, input_model())

        elif env['REQUEST_METHOD'] == 'DELETE':
            return db_delete_sample_item(instance_id)
        
        else:
            raise RequestError('invalid request method', '405 Method Not Allowed')

    # model routes #

    elif re.match(r'/api/sample/sample-item', env['PATH_INFO']):
        if env['REQUEST_METHOD'] == 'POST':
            result_id = db_create_sample_item(input_model())
            return {'id': result_id}
        
        elif env['REQUEST_METHOD'] == 'GET':
            query = parse_qs(env['QUERY_STRING'])
            return db_list_sample_item(offset=int(query.get('offset', 0)), limit=int(query.get('limit', 25)))
    
        else:
            raise RequestError('invalid request method', '405 Method Not Allowed')

#
# entry point
#

def application(env, start_response):

    try:
        body = routes(env)
        status_code = '201 Created' if body is None else '200 OK'

    except RequestError as e:
        body = {'error': e.msg}
        status_code = e.status
    
    start_response(status_code, [('Content-Type','application/json')])
    return [json.dumps(body).encode('utf-8')]
