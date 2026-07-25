import lingolib.parsing.symbols as symbols

from lingolib.errors import LingoSyntaxError
from .state import get_yaml_line


def parse_expr_str(ctx, data: dict, L_SRC: str, create_expression_ast):
    return symbols.L_SYM_str(
        object=create_expression_ast(ctx, data['str'], f'{L_SRC}.str.object'),
        L_SRC=f'{L_SRC}.str',
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data['str'])
    )


def parse_expr_concat(ctx, data: dict, L_SRC: str, create_expression_ast, src_info):
    if isinstance(data['concat'], list):
        ctx.log.debug(f'create_expression_ast_from_dict - concat expression: {data["concat"]!r}')
        return symbols.L_SYM_concat(
            items=create_expression_ast(ctx, data['concat'], f'{L_SRC}.concat.items'),
            L_SRC=f'{L_SRC}.concat',
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['concat'])
        )
    else:
        raise LingoSyntaxError(f'concat symbol must have a list {src_info()}')


def parse_expr_join(ctx, data: dict, L_SRC: str, create_expression_ast, src_info):
    ctx.log.debug(f'create_expression_ast_from_dict - join expression: {data}')
    args = {
        'L_SRC': f'{L_SRC}.join',
        'L_FILE': ctx.interpreter.file,
        'L_LINE': get_yaml_line(data)
    }

    for arg in data['join'].keys():
        match arg:
            case 'items':
                args['items'] = create_expression_ast(ctx, data['join']['items'], f'{L_SRC}.join.items')
            case 'separator':
                args['separator'] = create_expression_ast(ctx, data['join']['separator'], f'{L_SRC}.join.separator')
            case _:
                raise LingoSyntaxError(f'join symbol does not support key: {arg!r}{src_info()}')

    return symbols.L_SYM_join(**args)
