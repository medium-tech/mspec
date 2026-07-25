import lingolib.parsing.symbols as symbols

from lingolib.errors import LingoSyntaxError
from .state import get_yaml_line


def parse_expr_eq(ctx, data: dict, L_SRC: str, create_expression_ast, src_info):
    try:
        a_expr = data['eq']['a']
        b_expr = data['eq']['b']
    except KeyError as e:
        raise LingoSyntaxError(f'eq symbol missing key: {e}{src_info()}') from None

    return symbols.L_SYM_eq(
        a=create_expression_ast(ctx, a_expr, f'{L_SRC}.eq.a'),
        b=create_expression_ast(ctx, b_expr, f'{L_SRC}.eq.b'),
        L_SRC=f'{L_SRC}.eq',
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data['eq'])
    )


def parse_expr_int(ctx, data: dict, L_SRC: str, create_expression_ast, src_info):
    keys = set(data.keys())
    args = {
        'L_SRC': f'{L_SRC}.int',
        'L_FILE': ctx.interpreter.file,
        'L_LINE': get_yaml_line(data)
    }

    for key in keys:
        match key:
            case 'int':
                args['number'] = create_expression_ast(ctx, data['int'], f'{L_SRC}.int.number')
            case 'base':
                args['base'] = create_expression_ast(ctx, data['base'], f'{L_SRC}.int.base')
            case _:
                raise LingoSyntaxError(f'int symbol does not support key: {key!r}{src_info()}')

    return symbols.L_SYM_int(**args)


def parse_expr_add(ctx, data: dict, L_SRC: str, create_expression_ast, src_info):
    keys = set(data.keys())

    try:
        a_expr = data['add']['a']
        b_expr = data['add']['b']
    except KeyError as e:
        raise LingoSyntaxError(f'add symbol missing arg key: {e}{src_info()}') from None

    if len(keys) != 1:
        raise LingoSyntaxError(f'add symbol does not support root keys other than add, got: {keys!r}{src_info()}')
    elif len(data['add'].keys()) != 2:
        raise LingoSyntaxError(f'add symbol requires exactly two arg keys: a and b, got: {list(data["add"].keys())!r}{src_info()}')

    return symbols.L_SYM_add(
        a=create_expression_ast(ctx, a_expr, f'{L_SRC}.add.a'),
        b=create_expression_ast(ctx, b_expr, f'{L_SRC}.add.b'),
        L_SRC=f'{L_SRC}.add',
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data['add'])
    )
