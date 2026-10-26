import json
import os
from getpass import getpass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from lingolib.context import LingoContext, LingoRegisteredFunction
from lingolib.errors import LingoRuntimeError, LingoSyntaxError
from lingolib.parsing import LingoASTAppSpec
from lingolib.runtime.registry import (
    add_lib_to_registry,
    init_registry,
)
from lingolib.runtime.shared import DEFAULT_HOST, DEFAULT_PORT, convert_cli_value
from lingolib.symbols import L_SYM_func


def parse_cli_params(
    func: L_SYM_func,
    assignments: list[str],
    interactive: bool = False,
) -> dict:
    if func.args is None:
        raise LingoRuntimeError(f'op {func.name!r} has no parameter definitions')
    definitions = {arg.name: arg for arg in func.args}
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
            raise LingoRuntimeError(f'unknown parameter for op {func.name!r}: {name!r}')
        
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


def redact_secure_output(value: object, definition, show: bool = False) -> object:
    if show is True:
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


def call_op(op_reference: str, request_body: str) -> object:
    if op_reference.count('.') != 1:
        raise LingoRuntimeError(
            f'op must be specified as <module>.<op>, got {op_reference!r}'
        )

    module_name, op_name = op_reference.split('.')
    if not module_name or not op_name:
        raise LingoRuntimeError(
            f'op must be specified as <module>.<op>, got {op_reference!r}'
        )

    try:
        parsed_body = json.loads(request_body)
    except json.JSONDecodeError as e:
        raise LingoRuntimeError(f'invalid JSON request body: {e}') from None
    if not isinstance(parsed_body, dict) or any(
        not isinstance(key, str) for key in parsed_body
    ):
        raise LingoRuntimeError('--json must contain a JSON object with string keys')

    server_host = os.environ.get('LINGO_SERVER_HOST', DEFAULT_HOST)
    server_port = os.environ.get('LINGO_SERVER_PORT', DEFAULT_PORT)
    base_url = os.environ.get(
        'LINGO_CLIENT_HOST',
        f'http://{server_host}:{server_port}',
    ).rstrip('/')
    url = f'{base_url}/{quote(module_name, safe="")}/{quote(op_name, safe="")}'
    request = Request(
        url,
        data=request_body.encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
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


def evaluate_client_spec(
    ctx: LingoContext,
    ast: LingoASTAppSpec,
    op_reference: str,
    request_body: str | None = None,
    params: list[str] | None = None,
    interactive: bool = False,
    show_secure: bool = False,
) -> object:
    if op_reference.count('.') != 1:
        raise LingoSyntaxError(
            f'op must be specified as <module>.<op>, got {op_reference!r}'
        )
    module_name, op_name = op_reference.split('.')
    module = ast.modules.members.get(module_name)
    if module is None or op_name not in module.ops.funcs:
        raise LingoSyntaxError(f'op not found in app spec: {op_reference!r}')
    op_symbol = module.ops.funcs[op_name]

    if request_body is not None and (params is not None or interactive):
        raise LingoSyntaxError('request_body cannot be combined with params or interactive')

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

    if params is not None or interactive:
        request_body = json.dumps(
            parse_cli_params(op_symbol, params or [], interactive=interactive)
        )

    if request_body is None:
        raise LingoSyntaxError('request body is required; use params or interactive mode')
    
    response = call_op(op_reference, request_body)
    return redact_secure_output(response, op_symbol.return_, show=show_secure)


def print_response(response: object) -> None:
    print(json.dumps(response, indent=4, ensure_ascii=False))