import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing.spec_expression import create_expression_ast
from lingolib.parsing.state import get_yaml_line
from lingolib.types import LingoListDisplayOptions


def parse_define_symbol(
    ctx: LingoContext,
    name: str,
    data: dict,
    L_SRC: str,
) -> symbols.L_SYM_define:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'define symbol for {name!r} must be a mapping, got: {type(data).__name__!r}')

    try:
        define_type = data['define']
    except KeyError:
        raise LingoSyntaxError(f'define symbol for {name!r} missing required key: define') from None

    if not isinstance(define_type, str):
        raise LingoSyntaxError(f'define type for {name!r} must be string, got: {type(define_type).__name__!r}')

    args = {
        'L_SRC': f'{L_SRC}.define',
        'name': name,
        'type': define_type,
        'L_FILE': ctx.parser.file,
        'L_LINE': get_yaml_line(data)
    }

    if 'default' in data:
        args['default'] = create_expression_ast(ctx, data['default'], f'{L_SRC}.default')

    if 'element_type' in data:
        if not isinstance(data['element_type'], str):
            raise LingoSyntaxError(f'element_type for {name!r} must be string, got: {type(data["element_type"]).__name__!r}')
        args['element_type'] = data['element_type']

    if 'display' in data:
        if not isinstance(data['display'], dict):
            raise LingoSyntaxError(f'display for {name!r} must be mapping, got: {type(data["display"]).__name__!r}')
        args['display'] = LingoListDisplayOptions.from_dict(data['display'])

    if 'description' in data:
        if not isinstance(data['description'], str):
            raise LingoSyntaxError(f'description for {name!r} must be string, got: {type(data["description"]).__name__!r}')
        args['description'] = data['description']

    if 'fields' in data:
        if define_type != 'struct':
            raise LingoSyntaxError(f'fields key is only valid for struct defines, got type {define_type!r} for {name!r}')

        fields_data = data['fields']
        if not isinstance(fields_data, dict):
            raise LingoSyntaxError(f'fields for {name!r} must be a mapping, got: {type(fields_data).__name__!r}')

        args['fields'] = {
            field_name: parse_define_symbol(ctx, field_name, field_data, f'{L_SRC}.fields.{field_name}')
            for field_name, field_data in fields_data.items()
        }

    allowed_keys = {'define', 'type', 'default', 'element_type', 'display', 'description', 'fields'}
    unsupported = set(data.keys()) - allowed_keys
    if unsupported:
        raise LingoSyntaxError(f'unsupported key(s) in define block for {name!r}: {", ".join(sorted(unsupported))}')

    return symbols.L_SYM_define(**args)


def parse_func_symbol(ctx: LingoContext, name: str, data: dict) -> symbols.L_SYM_func:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'ops function {name!r} must be a mapping, got: {type(data).__name__!r}')

    try:
        func_expr_data = data['func']
    except KeyError:
        raise LingoSyntaxError(f'ops function {name!r} missing required key: func') from None

    parsed_func_expr = create_expression_ast(ctx, func_expr_data, f'ops.{name}.func')

    try:
        return_data = data['return']
    except KeyError:
        raise LingoSyntaxError(f'ops function {name!r} missing required key: return') from None

    return_symbol = parse_define_symbol(ctx, f'{name}.return', return_data, f'ops.{name}.return')
    
    args_data = data.get('args', {})
    if not isinstance(args_data, dict):
        raise LingoSyntaxError(f'args block for ops function {name!r} must be a mapping, got: {type(args_data).__name__!r}')

    parsed_args = []
    for arg_name, arg_data in args_data.items():
        parsed_args.append(parse_define_symbol(ctx, arg_name, arg_data, f'ops.{name}.args.{arg_name}'))

    return symbols.L_SYM_func(
        L_SRC=f'ops.{name}',
        name=name,
        args=parsed_args,
        func=parsed_func_expr,
        return_=return_symbol,
        description=data.get('description', ''),
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data)
    )


def parse_imports_symbol(ctx: LingoContext, data: list) -> symbols.L_SYM_imports:
    if not isinstance(data, list):
        raise LingoSyntaxError(f'imports symbol must be a list, got: {type(data).__name__!r}')

    for index, item in enumerate(data):
        if not isinstance(item, str):
            raise LingoSyntaxError(f'imports[{index}] must be a string, got: {type(item).__name__!r}')

    return symbols.L_SYM_imports(
        L_SRC='imports',
        paths=data,
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data)
    )