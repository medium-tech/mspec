import os
import re
import time
import json

from traceback import format_exc
from typing import NamedTuple

from mapp.context import get_context_from_env, MappContext, RequestContext, spec_from_env
from mapp.errors import *
from mapp.types import JSONResponse, PlainTextResponse, StaticFileResponse, to_json
from mapp.module.model.db import db_model_create_table
from mapp.module.model.server import create_model_routes
from mapp.module.op.server import create_op_routes
from mspec.core import get_mapp_ui_files, load_browser2_spec

import uwsgi

#
# debug
#

MAPP_SERVER_DEVELOPMENT_MODE = os.environ.get('MAPP_SERVER_DEVELOPMENT_MODE', 'false').lower() in ['true', 't', '1', 'yes', 'y']

def debug_page(server: MappContext, request: RequestContext):
    main_col = 36
    header_col = 42

    output = 'Debug Info\n\n'

    output += 'Request id: ' + request.request_id + '\n\n'

    try:
        access_token = server.current_access_token()
        authorization = '*' * len(access_token)
    except Exception as e:
        authorization = f'{e.__class__.__name__}: {str(e)}'

    output += f'Authorization:\n :: {authorization}\n\n'

    output += 'MappContext:\n'
    output += f' :: {"MappContext.server_port": <{main_col}}:: {server.server_port}\n'
    output += f' :: {"MappContext.client.host": <{main_col}}:: {server.client.host}\n'
    output += f' :: {"MappContext.current_access_token": <{main_col}}:: {str(type(server.current_access_token))}\n'
    output += f' :: {"MappContext.log": <{main_col}}:: {str(type(server.log))}\n\n'
    output += f' :: {"MappContext.db": <{main_col}}:: {str(type(server.db))}\n'
    output += f'   :: {"DBContext.db_url": <{header_col}}:: {str(server.db.db_url)}\n'
    output += f'   :: {"DBContext.connection": <{header_col}}:: {str(type(server.db.connection))}\n'
    output += f'   :: {"DBContext.cursor": <{header_col}}:: {str(type(server.db.cursor))}\n'
    output += f'   :: {"DBContext.commit": <{header_col}}:: {str(type(server.db.commit))}\n\n'
    output += f'RequestContext.raw_req_body ::{str(type(request.raw_req_body))} {len(request.raw_req_body)=}\n'
    output += 'RequestContext.env ::\n\n'

    for key in request.env:
        if key == 'HTTP_AUTHORIZATION':
            output += f' :: {key:<{header_col}}:: {"*" * len(request.env[key])}\n'
        else:
            output += f' :: {key:<{header_col}}:: {request.env[key]}\n'

    output += '\n'

    debug_delay = os.environ.get('DEBUG_DELAY', None)
    output += f'DEBUG_DELAY :: {debug_delay}\n\n'

    return output

def debug_routes(server: MappContext, request: RequestContext):
    path = request.env['PATH_INFO']
    # /api/debug (no exception name): show debug_page output
    if path.rstrip('/') == '/api/debug':
        raise PlainTextResponse('200 OK', debug_page(server, request))

    # /api/debug/<ExceptionName>: throw example exception
    match = re.match(r'/api/debug/([a-zA-Z_]+)$', path)
    if not match:
        return

    exc_name = match.group(1)
    if exc_name == 'PlainTextResponse':
        raise PlainTextResponse('200 OK', 'This is a plain text debug response')
    elif exc_name == 'JSONResponse':
        raise JSONResponse('200 OK', {'message': 'This is a JSON debug response'})
    elif exc_name == 'NotFoundError':
        raise NotFoundError('Debug: NotFoundError thrown')
    elif exc_name == 'AuthenticationError':
        raise AuthenticationError('Debug: AuthenticationError thrown')
    elif exc_name == 'ForbiddenError':
        raise ForbiddenError('Debug: ForbiddenError thrown')
    elif exc_name == 'MappValidationError':
        raise MappValidationError('Debug: MappValidationError thrown', {'field': 'example error'})
    elif exc_name == 'RequestError':
        raise RequestError('Debug: RequestError thrown')
    elif exc_name == 'Exception':
        raise Exception('This error should not be shown to user')
    else:
        raise NotFoundError(f'Debug: Exception \'{exc_name}\' not found')


#
# context
#

main_ctx = get_context_from_env()
main_ctx.log = uwsgi.log

#
# init server routes
#

route_list = []

mapp_spec = spec_from_env()

try:
    spec_modules = mapp_spec['modules']
except KeyError:
    raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

for module in spec_modules.values():
    if module.get('hidden', False) is True:
        continue

    for model in module.get('models', {}).values():
        if model.get('hidden', False) is True:
            continue

        route_resolver, model_class = create_model_routes(module, model)
        route_list.append(route_resolver)
        db_model_create_table(main_ctx, model_class)

    for op in module.get('ops', {}).values():
        if op.get('hidden', False) is True:
            continue
        route_resolver = create_op_routes(module, op)
        route_list.append(route_resolver)

if MAPP_SERVER_DEVELOPMENT_MODE is True:
    route_list.append(debug_routes)

#
# generate dynamic index.html
#

def generate_index_html(spec: dict) -> str:
    """
    Generate the index.html page with embedded Lingo JSON spec.
    """

    # init spec #
    
    lingo_index_page = load_browser2_spec('builtin-mapp-project.json')
    
    project_name = spec['project']['name']['lower_case']
    module_names = [module['name']['kebab_case'] for module in spec['modules'].values() if not module.get('hidden', False)]
    
    lingo_params = {
        'project_name': project_name,
        'module_names': module_names
    }
    
    # genereate html and embed spec #

    lingo_spec_json = json.dumps(lingo_index_page, indent=4)
    lingo_params_json = json.dumps(lingo_params, indent=4)
    

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="lingo-app" class="lingo-container">
        <p>Loading...</p>
    </div>
    
    <!-- Embedded Lingo spec -->
    <script type="application/json" id="lingoSpec">
{lingo_spec_json}
    </script>
    
    <!-- Embedded Lingo params -->
    <script type="application/json" id="lingoParams">
{lingo_params_json}
    </script>
    
    <script src="markup.js"></script>
    
    <script>
        // Retrieve and parse the embedded spec and params
        const specText = document.getElementById('lingoSpec').textContent;
        const paramsText = document.getElementById('lingoParams').textContent;
        const lingoSpec = JSON.parse(specText);
        const lingoParams = JSON.parse(paramsText);
        
        // Run the lingo app on load
        window.addEventListener('load', () => {{
            try {{
                const app = lingoApp(lingoSpec, lingoParams, {{}});
                renderLingoApp(app, document.getElementById('lingo-app'));
            }} catch (error) {{
                console.error('Failed to initialize Lingo app:', error);
                document.getElementById('lingo-app').innerHTML = `<p style="color: red;">Error: ${{error.message}}</p>`;
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_module_html(spec: dict, module_key: str) -> str:
    """
    Generate the module page with embedded Lingo JSON spec.
    """

    # init spec #
    
    lingo_module_page = load_browser2_spec('builtin-mapp-module.json')
    
    project_name = spec['project']['name']['lower_case']
    module = spec['modules'][module_key]
    module_name = module['name']['kebab_case']
    
    # get model names and op names for this module
    model_names = [model['name']['kebab_case'] for model in module.get('models', {}).values() if not model.get('hidden', False)]
    op_names = [op['name']['kebab_case'] for op in module.get('ops', {}).values() if not op.get('hidden', False)]
    
    lingo_params = {
        'project_name': project_name,
        'module_name': module_name,
        'model_names': model_names,
        'op_names': op_names
    }
    
    # generate html and embed spec #

    lingo_spec_json = json.dumps(lingo_module_page, indent=4)
    lingo_params_json = json.dumps(lingo_params, indent=4)
    

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - {module_name}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div id="lingo-app" class="lingo-container">
        <p>Loading...</p>
    </div>
    
    <!-- Embedded Lingo spec -->
    <script type="application/json" id="lingoSpec">
{lingo_spec_json}
    </script>
    
    <!-- Embedded Lingo params -->
    <script type="application/json" id="lingoParams">
{lingo_params_json}
    </script>
    
    <script src="/markup.js"></script>
    
    <script>
        // Retrieve and parse the embedded spec and params
        const specText = document.getElementById('lingoSpec').textContent;
        const paramsText = document.getElementById('lingoParams').textContent;
        const lingoSpec = JSON.parse(specText);
        const lingoParams = JSON.parse(paramsText);
        
        // Run the lingo app on load
        window.addEventListener('load', () => {{
            try {{
                const app = lingoApp(lingoSpec, lingoParams, {{}});
                renderLingoApp(app, document.getElementById('lingo-app'));
            }} catch (error) {{
                console.error('Failed to initialize Lingo app:', error);
                document.getElementById('lingo-app').innerHTML = `<p style="color: red;">Error: ${{error.message}}</p>`;
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_model_html(spec: dict, module_key: str, model_key: str) -> str:
    """
    Generate the model page with embedded Lingo JSON spec.
    """

    # init spec #
    
    lingo_model_page = load_browser2_spec('builtin-mapp-model.json')
    
    project_name = spec['project']['name']['lower_case']
    module = spec['modules'][module_key]
    module_name = module['name']['kebab_case']
    model = module['models'][model_key]
    model_name = model['name']['kebab_case']
    
    lingo_params = {
        'project_name': project_name,
        'module_name': module_name,
        'model_name': model_name,
        'model_definition': model
    }
    
    # generate html and embed spec #

    lingo_spec_json = json.dumps(lingo_model_page, indent=4)
    lingo_params_json = json.dumps(lingo_params, indent=4)
    

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - {module_name} - {model_name}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div id="lingo-app" class="lingo-container">
        <p>Loading...</p>
    </div>
    
    <!-- Embedded Lingo spec -->
    <script type="application/json" id="lingoSpec">
{lingo_spec_json}
    </script>
    
    <!-- Embedded Lingo params -->
    <script type="application/json" id="lingoParams">
{lingo_params_json}
    </script>
    
    <script src="/markup.js"></script>
    
    <script>
        // Retrieve and parse the embedded spec and params
        const specText = document.getElementById('lingoSpec').textContent;
        const paramsText = document.getElementById('lingoParams').textContent;
        const lingoSpec = JSON.parse(specText);
        const lingoParams = JSON.parse(paramsText);
        
        // Run the lingo app on load
        window.addEventListener('load', () => {{
            try {{
                const app = lingoApp(lingoSpec, lingoParams, {{}});
                renderLingoApp(app, document.getElementById('lingo-app'));
            }} catch (error) {{
                console.error('Failed to initialize Lingo app:', error);
                document.getElementById('lingo-app').innerHTML = `<p style="color: red;">Error: ${{error.message}}</p>`;
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_op_html(spec: dict, module_key: str, op_key: str) -> str:
    """
    Generate the op page with embedded Lingo JSON spec.
    """

    # init spec #
    
    lingo_op_page = load_browser2_spec('builtin-mapp-op.json')
    
    project_name = spec['project']['name']['lower_case']
    module = spec['modules'][module_key]
    module_name = module['name']['kebab_case']
    op = module['ops'][op_key]
    op_name = op['name']['kebab_case']
    
    lingo_params = {
        'project_name': project_name,
        'module_name': module_name,
        'op_name': op_name,
        'op_definition': op
    }
    
    # generate html and embed spec #

    lingo_spec_json = json.dumps(lingo_op_page, indent=4)
    lingo_params_json = json.dumps(lingo_params, indent=4)
    

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - {module_name} - {op_name}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div id="lingo-app" class="lingo-container">
        <p>Loading...</p>
    </div>

    <!-- Embedded Lingo spec -->
    <script type="application/json" id="lingoSpec">
{lingo_spec_json}
    </script>
    
    <!-- Embedded Lingo params -->
    <script type="application/json" id="lingoParams">
{lingo_params_json}
    </script>
    
    <script src="/markup.js"></script>
    
    <script>
        // Retrieve and parse the embedded spec and params
        const specText = document.getElementById('lingoSpec').textContent;
        const paramsText = document.getElementById('lingoParams').textContent;
        const lingoSpec = JSON.parse(specText);
        const lingoParams = JSON.parse(paramsText);
        
        // Run the lingo app on load
        window.addEventListener('load', () => {{
            try {{
                const app = lingoApp(lingoSpec, lingoParams, {{}});
                renderLingoApp(app, document.getElementById('lingo-app'));
            }} catch (error) {{
                console.error('Failed to initialize Lingo app:', error);
                document.getElementById('lingo-app').innerHTML = `<p style="color: red;">Error: ${{error.message}}</p>`;
            }}
        }});
    </script>
</body>
</html>'''
    
    return html

def generate_model_instance_html(spec: dict, module_key: str, model_key: str, url: str) -> str:
    """
    Generate the model instance page with embedded Lingo JSON spec.
    """

    # init spec #
    
    lingo_model_instance_page = load_browser2_spec('builtin-mapp-model-instance.json')
    
    project_name = spec['project']['name']['lower_case']
    module = spec['modules'][module_key]
    module_name = module['name']['kebab_case']
    model = module['models'][model_key]
    model_name = model['name']['kebab_case']

    url_split = url.strip('/').split('/')
    model_id = url_split[-1]
    
    lingo_params = {
        'project_name': project_name,
        'module_name': module_name,
        'model_name': model_name,
        'model_definition': model,
        'model_id': model_id
    }
    
    # generate html and embed spec #

    lingo_spec_json = json.dumps(lingo_model_instance_page, indent=4)
    lingo_params_json = json.dumps(lingo_params, indent=4)
    

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Model - {model_id}</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div id="lingo-app" class="lingo-container">
        <p>Loading...</p>
    </div>
    
    <!-- Embedded Lingo spec -->
    <script type="application/json" id="lingoSpec">
{lingo_spec_json}
    </script>
    
    <!-- Embedded Lingo params -->
    <script type="application/json" id="lingoParams">
{lingo_params_json}
    </script>
    
    <script src="/markup.js"></script>
    
    <script>
        // Retrieve and parse the embedded spec and params
        const specText = document.getElementById('lingoSpec').textContent;
        const paramsText = document.getElementById('lingoParams').textContent;
        const lingoSpec = JSON.parse(specText);
        const lingoParams = JSON.parse(paramsText);
        
        // Run the lingo app on load
        window.addEventListener('load', () => {{
            try {{
                const app = lingoApp(lingoSpec, lingoParams, {{}});
                renderLingoApp(app, document.getElementById('lingo-app'));
            }} catch (error) {{
                console.error('Failed to initialize Lingo app:', error);
                document.getElementById('lingo-app').innerHTML = `<p style="color: red;">Error: ${{error.message}}</p>`;
            }}
        }});
    </script>
</body>
</html>'''
    
    return html


#
# load static ui files
#

class StaticFileData(NamedTuple):
    content: bytes
    content_type: str

static_files = {}
dynamic_files = []

ui_src_dir = os.environ.get('MAPP_UI_FILE_SOURCE', None)

for file_path in get_mapp_ui_files(ui_src_dir):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # determine content type #
    if file_path.suffix == '.html':
        content_type = 'text/html'
    elif file_path.suffix == '.css':
        content_type = 'text/css'
    elif file_path.suffix == '.js':
        content_type = 'application/javascript'
    else:
        content_type = 'application/octet-stream'
    
    static_files[file_path.name] = StaticFileData(
        content=content,
        content_type=content_type
    )

# add generated index.html to static files #
index_html_content = generate_index_html(mapp_spec)
static_files['index.html'] = StaticFileData(
    content=index_html_content.encode('utf-8'),
    content_type='text/html'
)

# add generated module pages to static files #
for module_key, module in mapp_spec['modules'].items():
    if module.get('hidden', False) is True:
        continue
    
    module_kebab = module['name']['kebab_case']
    module_html_content = generate_module_html(mapp_spec, module_key)
    static_files[module_kebab] = StaticFileData(
        content=module_html_content.encode('utf-8'),
        content_type='text/html'
    )
    
    # add dynamic and static model pages #
    for model_key, model in module.get('models', {}).items():
        if model.get('hidden', False) is True:
            continue
        
        model_kebab = model['name']['kebab_case']
        model_html_content = generate_model_html(mapp_spec, module_key, model_key)
        static_files[f'{module_kebab}/{model_kebab}'] = StaticFileData(
            content=model_html_content.encode('utf-8'),
            content_type='text/html'
        )

        pattern = f'/{module_kebab}/{model_kebab}/[0-9a-zA-Z]+$'

        dynamic_files.append((
            re.compile(pattern),
            generate_model_instance_html,
            mapp_spec,
            module_key,
            model_key
        ))

    # add static op pages #
    for op_key, op in module.get('ops', {}).items():

        if op.get('hidden', False) is True:
            continue

        op_kebab = op['name']['kebab_case']
        op_html_content = generate_op_html(mapp_spec, module_key, op_key)
        static_files[f'{module_kebab}/{op_kebab}'] = StaticFileData(
            content=op_html_content.encode('utf-8'),
            content_type='text/html'
        )

def static_routes(server: MappContext, request: RequestContext):
    """resolve static file routes"""
    
    path_stripped = request.env['PATH_INFO'].strip('/')
    path = 'index.html' if path_stripped == '' else path_stripped
    
    try:
        file_data = static_files[path]
    except KeyError:
        pass
    else:
        raise StaticFileResponse('200 OK', file_data.content, file_data.content_type)
    
def dynamic_file_routes(server: MappContext, request: RequestContext):
    """resolve dynamic file routes"""

    for pattern, generator_func, *gen_args in dynamic_files:
        if pattern.match(request.env['PATH_INFO']):
            mapp_spec, module_key, model_key = gen_args
    
            html_content = generator_func(mapp_spec, module_key, model_key, request.env['PATH_INFO'])
            raise StaticFileResponse(
                '200 OK',
                content=html_content.encode('utf-8'),
                content_type='text/html'
            )

route_list.append(static_routes)
route_list.append(dynamic_file_routes)

#
# wsgi application
#

def application(env, start_response):

    # user from authorization header #

    def access_token_from_request():
        # expecting HTTP_AUTHORIZATION: 'Bearer <token>'
        try:
            auth_header = env['HTTP_AUTHORIZATION']
        except KeyError:
            raise AuthenticationError('Not logged in')
        
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError('Invalid authorization header')
        
        return auth_header[7:]

    # init request context #
    
    assert main_ctx.current_access_token is None

    server_ctx = MappContext(
        server_port=main_ctx.server_port,
        client=main_ctx.client,
        db=main_ctx.db,
        log=main_ctx.log
    )

    assert server_ctx.current_access_token is None
    
    server_ctx.current_access_token = access_token_from_request

    # init request logging #

    request_id = f'{time.time_ns()}-{os.getpid()}'
    request_start = time.time()
    server_ctx.log(f':: REQ :: {request_id} :: {env["REQUEST_METHOD"]} - {env["PATH_INFO"]}')

    request = RequestContext(
        env=env,
        # best practice is to always consume body if it exists: https://uwsgi-docs.readthedocs.io/en/latest/ThingsToKnow.html
        raw_req_body=env['wsgi.input'].read(),
        request_id=request_id
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

        except StaticFileResponse as e:
            body = e.content
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
            body = e.to_dict()
            status_code = '401 Unauthorized'
            content_type = JSONResponse.content_type
            break

        except ForbiddenError as e:
            body = e.to_dict()
            status_code = '403 Forbidden'
            content_type = JSONResponse.content_type
            break

        except MappValidationError as e:
            body = e.to_dict()
            status_code = '400 Bad Request'
            content_type = JSONResponse.content_type
            break

        except MappUserError as e:
            body = e.to_dict()
            status_code = '400 Bad Request'
            content_type = JSONResponse.content_type
            break

        except RequestError as e:
            body = e.to_dict()
            status_code = '400 Bad Request'
            content_type = JSONResponse.content_type 
            break

        # uncaught exception | internal server error #

        except Exception as e:
            body = {
                'error': {
                    'code': 'INTERNAL_SERVER_ERROR',
                    'message': 'Contact support or check logs for details',
                    'request_id': str(request_id)
                }
            }
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

    elapsed_time = time.time() - request_start

    server_ctx.log(f':: RESP :: {request_id} :: {status_code} :: {elapsed_time:.4f}s')

    start_response(status_code, [('Content-Type', content_type)])

    if content_type == JSONResponse.content_type:
        return [to_json(body).encode('utf-8')]
    elif isinstance(body, bytes):
        return [body]
    else:
        return [body.encode('utf-8')]
