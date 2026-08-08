import lingolib.parsing.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoListDisplayOptions

from .ast import LingoASTGUISpec
from .state import get_yaml_line
from .expr import create_expression_ast


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
        raise LingoSyntaxError(f'missing required define key for {name!r}') from None

    if not isinstance(define_type, str):
        raise LingoSyntaxError(f'define type for {name!r} must be string, got: {type(define_type).__name__!r}')

    args = {
        'L_SRC': f'{L_SRC}.define',
        'name': name,
        'type': define_type,
        'L_FILE': ctx.interpreter.file,
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

    allowed_keys = {'define', 'default', 'element_type', 'display', 'description'}
    unsupported = set(data.keys()) - allowed_keys
    if unsupported:
        raise LingoSyntaxError(f'unsupported key(s) in define block for {name!r}: {", ".join(sorted(unsupported))}')

    return symbols.L_SYM_define(**args)


def parse_state_symbol(ctx: LingoContext, data: dict) -> symbols.L_SYM_state:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'state symbol must be a mapping, got: {type(data).__name__!r}')

    fields = {}
    for field_name, field_data in data.items():
        if not isinstance(field_name, str):
            raise LingoSyntaxError(f'state field names must be strings, got: {type(field_name).__name__!r}')
        fields[field_name] = parse_define_symbol(ctx, field_name, field_data, f'state.{field_name}')

    return symbols.L_SYM_state(
        L_SRC='state',
        fields=fields,
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data)
    )


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
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data)
    )


def parse_ops_symbol(ctx: LingoContext, data: dict) -> symbols.L_SYM_ops:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'ops symbol must be a mapping, got: {type(data).__name__!r}')

    funcs = {}
    for func_name, func_data in data.items():
        if not isinstance(func_name, str):
            raise LingoSyntaxError(f'ops function names must be strings, got: {type(func_name).__name__!r}')
        funcs[func_name] = parse_func_symbol(ctx, func_name, func_data)

    return symbols.L_SYM_ops(
        L_SRC='ops',
        funcs=funcs,
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data)
    )


def spec_gui_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict
) -> LingoASTGUISpec:

    ctx.log.debug('spec_gui_ast_from_dict')

    try:
        block_data = data['block']
    except KeyError:
        raise LingoSyntaxError('missing block symbol')

    if not isinstance(block_data, list):
        raise LingoSyntaxError(f'block symbol must be a list, got: {type(block_data).__name__!r}')

    block_items = []
    for index, item in enumerate(block_data):
        block_items.append(create_expression_ast(ctx, item, f'block[{index}]'))

    block = symbols.L_SYM_block(
        L_SRC='block',
        items=block_items,
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(block_data),
    )

    
    if 'state' in data:
        state_symbol = parse_state_symbol(ctx, data['state'])
    else:
        state_symbol = None

    if 'ops' in data:
        ops_symbol = parse_ops_symbol(ctx, data['ops'])
    else:
        ops_symbol = None

    return LingoASTGUISpec(lingo=lingo, block=block, state=state_symbol, ops=ops_symbol)
