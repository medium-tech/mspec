import json
import os

from getpass import getpass
from typing import NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from lingolib.context import LingoContext, LingoRegisteredFunction
from lingolib.errors import LingoRuntimeError, LingoSyntaxError
from lingolib.parsing import LingoASTAppSpec
from lingolib.runtime.registry import (
    add_lib_to_registry,
    init_registry,
    resolve_model_define,
)
from lingolib.runtime.shared import DEFAULT_HOST, DEFAULT_PORT, convert_cli_value
from lingolib.symbols import L_SYM_func


class ClientModelRequest(NamedTuple):
    model: str
    action: str
    item_id: str | None = None
    offset: int | None = None
    limit: int | None = None


MODEL_ACTIONS = ('create', 'list', 'get', 'put', 'patch', 'delete')


#
# cli parsing
#

def parse_cli_params(
    func: L_SYM_func,
    assignments: list[str],
    interactive: bool = False,
) -> dict:
    if func.args is None:
        raise LingoRuntimeError(f'op {func.name!r} has no parameter definitions')
    return _parse_assignments(
        {arg.name: arg for arg in func.args}, f'op {func.name!r}', assignments, interactive
    )

def _parse_assignments(
    definitions: dict,
    owner: str,
    assignments: list[str],
    interactive: bool,
) -> dict:
    parsed = {}

    # parse assignments from cli #

    for assignment in assignments:
        if '=' not in assignment:
            raise LingoRuntimeError(f'parameter must use name=value format, got {assignment!r}')
        
        name, raw_value = assignment.split('=', 1)
        if not name:
            raise LingoRuntimeError(f'parameter name cannot be empty: {assignment!r}')
            
        if name in parsed:
            raise LingoRuntimeError(f'parameter specified more than once: {name!r}')
        try:
            field_type = definitions[name].type
        except KeyError:
            raise LingoRuntimeError(f'unknown parameter for {owner}: {name!r}')
        
        parsed[name] = convert_cli_value(name, str(field_type), raw_value)

    # prompt for missing params #

    if interactive:
        for name, definition in definitions.items():

            # only prompt for missing params #

            if name in parsed or definition.default is not None:
                continue

            # build prompt #

            prompt = f'{name} ({definition.type})'
            if definition.description:
                prompt += f' - {definition.description}'
            prompt += ': '

            # prompt user up to 3 times #

            for _ in range(3):
                raw_value = (
                    getpass(prompt) if definition.secure else input(prompt)
                )
                try:
                    parsed[name] = convert_cli_value(
                        name, str(definition.type), raw_value
                    )
                    break
                except LingoRuntimeError as e:
                    if definition.secure:
                        print(f'Invalid value for secure parameter {name!r}; try again.')
                    else:
                        print(f'Invalid value: {e}')
            else:
                raise LingoRuntimeError(f'Max attempts reached for {name!r}')
        
    return parsed

#
# references
#

def _split_reference(reference: str, kind: str) -> tuple[str, str]:
    parts = reference.split('.')
    if len(parts) != 2 or not all(parts):
        raise LingoRuntimeError(f'{kind} must be specified as <module>.<{kind}>, got {reference!r}')
    return parts[0], parts[1]

def resolve_client_model(ctx: LingoContext, ast: LingoASTAppSpec, model_reference: str):
    module_name, model_name = _split_reference(model_reference, 'model')
    module = ast.modules.members.get(module_name)
    if module is None or model_name not in module.models:
        raise LingoSyntaxError(f'model not found in app spec: {model_reference!r}')

    if ctx.registry is None:
        init_registry(ctx)
    add_lib_to_registry(ctx, ast.imports)
    return resolve_model_define(ctx, module.models[model_name])

def resolve_client_op(ctx: LingoContext, ast: LingoASTAppSpec, op_reference: str) -> L_SYM_func:
    """return the func symbol for an app op, following a reference into the imported libs"""
    module_name, op_name = _split_reference(op_reference, 'op')
    module = ast.modules.members.get(module_name)
    if module is None or op_name not in module.ops.funcs:
        raise LingoSyntaxError(f'op not found in app spec: {op_reference!r}')

    op_symbol = module.ops.funcs[op_name]

    if op_symbol.reference is not None:
        if ctx.registry is None:
            init_registry(ctx)
        add_lib_to_registry(ctx, ast.imports)
        try:
            registered_op = ctx.registry.lib[op_symbol.reference]
        except KeyError:
            raise LingoSyntaxError(f'op reference not found in lib: {op_symbol.reference!r}') from None
        if not isinstance(registered_op, LingoRegisteredFunction):
            raise LingoSyntaxError(f'op reference is not a function: {op_symbol.reference!r}')
        op_symbol = registered_op.ast

    return op_symbol

#
# output
#

def redact_secure_output(value: object, definition, show: bool = False) -> object:
    # keys without a definition, such as a model's generated id, are not secure
    if show is True or definition is None:
        return value
    
    if definition.secure:
        return 'REDACTED'
    
    if isinstance(value, dict) and definition.fields:
        return {
            key: redact_secure_output(
                item, definition.fields.get(key), show=show
            )
            for key, item in value.items()
        }
    return value

def print_response(response: object) -> None:
    print(json.dumps(response, indent=4, ensure_ascii=False))

#
# request
#

def _base_url() -> str:
    server_host = os.environ.get('LINGO_SERVER_HOST', DEFAULT_HOST)
    server_port = os.environ.get('LINGO_SERVER_PORT', DEFAULT_PORT)
    return os.environ.get(
        'LINGO_CLIENT_HOST',
        f'http://{server_host}:{server_port}',
    ).rstrip('/')

def _validate_request_body(request_body: str) -> None:
    try:
        parsed_body = json.loads(request_body)
    except json.JSONDecodeError as e:
        raise LingoRuntimeError(f'invalid JSON request body: {e}') from None
    if not isinstance(parsed_body, dict) or any(
        not isinstance(key, str) for key in parsed_body
    ):
        raise LingoRuntimeError('--json must contain a JSON object with string keys')

def _request(method: str, path_parts: list[str], request_body: str | None = None, query: dict | None = None) -> object:
    url = f'{_base_url()}/' + '/'.join(quote(part, safe='') for part in path_parts)
    if query:
        url += f'?{urlencode(query)}'

    request = Request(
        url,
        data=None if request_body is None else request_body.encode('utf-8'),
        headers={'Content-Type': 'application/json'} if request_body is not None else {},
        method=method,
    )

    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
    except HTTPError as e:
        response_body = e.read().decode('utf-8', errors='replace')
        try:
            error_payload = json.loads(response_body)
        except json.JSONDecodeError:
            error_payload = response_body
        raise LingoRuntimeError(
            f'server returned HTTP {e.code}\n{json.dumps(error_payload, ensure_ascii=False)}'
        ) from None
    except URLError as e:
        raise LingoRuntimeError(f'failed to connect to Lingo server at {url}: {e.reason}') from None

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as e:
        raise LingoRuntimeError(f'server returned invalid JSON: {e}') from None

def fetch_server_spec() -> str:
    """fetch the original yaml app spec text from the server's GET /lingo/spec endpoint"""
    url = f'{_base_url()}/lingo/spec'
    try:
        with urlopen(Request(url, method='GET')) as response:
            return response.read().decode('utf-8')
    except HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise LingoRuntimeError(f'server returned HTTP {e.code}\n{body}') from None
    except URLError as e:
        raise LingoRuntimeError(f'failed to connect to Lingo server at {url}: {e.reason}') from None

def call_op(op_reference: str, request_body: str) -> object:
    module_name, op_name = _split_reference(op_reference, 'op')
    _validate_request_body(request_body)
    return _request('POST', [module_name, op_name], request_body)

def call_model(request: ClientModelRequest, request_body: str | None = None) -> object:

    module_name, model_name = _split_reference(request.model, 'model')
    path = [module_name, model_name]
    query = None

    match request.action:
        case 'create':
            method = 'POST'
        case 'list':
            method = 'GET'
            query = {
                name: value
                for name, value in (('offset', request.offset), ('limit', request.limit))
                if value is not None
            }
        case 'get' | 'put' | 'patch' | 'delete':
            method = request.action.upper()
            path.append(request.item_id)
        case _:
            raise LingoRuntimeError(f'unknown model action: {request.action!r}')

    if request_body is not None:
        _validate_request_body(request_body)

    return _request(method, path, request_body, query)

#
# evaluators
#

def _evaluate_model_request(
    ctx: LingoContext,
    ast: LingoASTAppSpec,
    model_request: ClientModelRequest,
    request_body: str | None,
    params: list[str] | None,
    interactive: bool,
    show_secure: bool,
) -> object:

    # init #

    action = model_request.action

    if action not in MODEL_ACTIONS:
        raise LingoSyntaxError(f'unknown model action: {action!r}')

    define = resolve_client_model(ctx, ast, model_request.model)

    # request body #

    needs_request_body = action in ('create', 'put', 'patch')

    if needs_request_body:
        if request_body is not None and (params is not None or interactive):
            raise LingoSyntaxError('request_body cannot be combined with params or interactive')
        if action == 'patch' and interactive:
            raise LingoSyntaxError('interactive mode cannot be used with patch')

        if params is not None or interactive:
            request_body = json.dumps(_parse_assignments(
                define.fields, f'model {model_request.model!r}', params or [], interactive
            ))
        if request_body is None:
            raise LingoSyntaxError(f'{action} requires a request body; use json, params or interactive mode')
        
    elif request_body is not None or params is not None or interactive:
        raise LingoSyntaxError(f'{action} does not accept a request body')

    # make request and handle response #

    response = call_model(model_request, request_body)

    if action == 'list':
        if not isinstance(response, dict) or not isinstance(response.get('items'), list):
            raise LingoRuntimeError('server returned an invalid list response')
        return {
            **response,
            'items': [redact_secure_output(item, define, show=show_secure) for item in response['items']],
        }
    
    return redact_secure_output(response, define, show=show_secure)

def _evaluate_op_request(
        ctx: LingoContext,
        ast: LingoASTAppSpec,
        op_reference: str,
        request_body: str | None = None,
        params: list[str] | None = None,
        interactive: bool = False,
        show_secure: bool = False,
) -> object:

    # init #
    
    if not isinstance(op_reference, str) or op_reference.count('.') != 1:
        raise LingoSyntaxError(f'op must be a string specified as <module>.<op>, got {op_reference!r}')

    if request_body is not None and (params is not None or interactive):
        raise LingoSyntaxError('request_body cannot be combined with params or interactive')

    # get op #

    op_symbol = resolve_client_op(ctx, ast, op_reference)

    # get input #

    if params is not None or interactive:
        request_body = json.dumps(
            parse_cli_params(op_symbol, params or [], interactive=interactive)
        )

    if request_body is None:
        raise LingoSyntaxError('request body is required; use params or interactive mode')

    # make request and handle response #
    
    response = call_op(op_reference, request_body)
    return redact_secure_output(response, op_symbol.return_, show=show_secure)

def evaluate_client_spec(
    ctx: LingoContext,
    ast: LingoASTAppSpec,
    op_reference: str | None,
    request_body: str | None = None,
    params: list[str] | None = None,
    interactive: bool = False,
    show_secure: bool = False,
    model_request: ClientModelRequest | None = None,
) -> object:
    if (op_reference is None) == (model_request is None):
        raise LingoSyntaxError('specify exactly one of op_reference or model_request')

    if model_request is not None:
        return _evaluate_model_request(ctx, ast, model_request, request_body, params, interactive, show_secure)
    else:
        return _evaluate_op_request(ctx, ast, op_reference, request_body, params, interactive, show_secure)