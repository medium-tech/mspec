from lingolib.constants import (
    MIN_LINE_BREAKS,
    MAX_LINE_BREAKS,
    MIN_HEADING_LEVEL,
    MAX_HEADING_LEVEL,
)
import lingolib.parsing.symbols as symbols


from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
import lingolib.parsing.symbols as symbols
from lingolib.types import LingoLiteralTypeNames, LingoLanguageError, LingoLiteralTypes, LingoPrimitiveTypes, LingoStyleOptions


from .state import get_yaml_line


def create_expression_ast(
    ctx: LingoContext,
    data: LingoLiteralTypes,
    L_SRC: str,
) -> symbols.ExpressionSymbols:

    if isinstance(data, LingoPrimitiveTypes):
        ctx.log.debug(f'create_expression_ast - literal: {data!r}')
        type_name = type(data).__name__
        value = data.replace(r'\n', '\n').replace(r'\t', '\t') if type_name == 'str' else data
        try:
            l_file = ctx.interpreter.file
            l_line = get_yaml_line(data)
        except AttributeError:
            l_file = ''
            l_line = -1

        return symbols.L_SYM_value(
            type=type_name,
            value=value,
            L_SRC=f'{L_SRC}.literal',
            L_FILE=l_file,
            L_LINE=l_line
        )

    elif isinstance(data, LingoLanguageError):
        ctx.log.debug(f'create_expression_ast - error: {data!r}')
        try:
            l_file = ctx.interpreter.file
            l_line = get_yaml_line(data)
        except AttributeError:
            l_file = ''
            l_line = -1

        return symbols.L_SYM_error(
            error=data.error,
            code=data.code,
            L_SRC=f'{L_SRC}.error',
            L_FILE=l_file,
            L_LINE=l_line
        )

    elif isinstance(data, list):
        ctx.log.debug(f'create_expression_ast - list: {data!r}')
        return [create_expression_ast(ctx, item, f'{L_SRC}[{i}]') for i, item in enumerate(data)]

    elif isinstance(data, dict):
        return parse_expression_ast_from_dict(
            ctx=ctx,
            data=data,
            L_SRC=L_SRC,
            # create_expression_ast=create_expression_ast,
        )

    else:
        raise LingoSyntaxError(f'unsupported expression type: {type(data).__name__!r}')


# def create_expression_ast_from_dict(
#     ctx: LingoContext,
#     data: dict,
#     L_SRC: str,
#     create_expression_ast,
# ) -> symbols.ExpressionSymbols:
#     return parse_expression_ast_from_dict(
#         ctx=ctx,
#         data=data,
#         L_SRC=L_SRC,
#         create_expression_ast=create_expression_ast,
#     )

def parse_expression_ast_from_dict(ctx, data: dict, L_SRC: str):
    keys = set(data.keys())
    ctx.log.debug(f'parse_expression_ast_from_dict - keys: {keys!r}')

    line_no = get_yaml_line(data)

    def src_info():
        msg = f"; '{L_SRC}'"
        if ctx.interpreter.file:
            msg += f' in file {ctx.interpreter.file!r}'
            if line_no != -1:
                msg += f' at line {line_no}'
        return msg

    if keys == {'handle'}:
        return symbols.L_SYM_handle(
            L_SRC=f'{L_SRC}.handle',
            expr=create_expression_ast(ctx, data['handle'], f'{L_SRC}.handle.expr'),
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['handle'])
        )

    elif 'error' in keys:
        args = {
            'L_SRC': f'{L_SRC}.error',
            'L_FILE': ctx.interpreter.file,
            'L_LINE': get_yaml_line(data)
        }
        for key in keys:
            match key:
                case 'error':
                    if isinstance(data['error'], str):
                        args['error'] = data['error']
                    else:
                        raise LingoSyntaxError(f'error field of error symbol must be a literal str value, expressions that return str are not supported{src_info()}')
                case 'code':
                    if isinstance(data['code'], str):
                        args['code'] = data['code']
                    else:
                        raise LingoSyntaxError(f'code field of error symbol must be a literal str value, expressions that return str are not supported{src_info()}')
                case _:
                    raise LingoSyntaxError(f'error symbol does not support key: {key!r}{src_info()}')
        return symbols.L_SYM_error(**args)

    elif 'value' in keys:

        if data['type'] not in LingoLiteralTypeNames:
            raise LingoSyntaxError(f'invalid type for value symbol: {data["type"]!r}{src_info()}')

        elif isinstance(data['value'], LingoPrimitiveTypes) and type(data['value']).__name__ != data['type']:
            raise LingoSyntaxError(f'value type mismatch: expected {data["type"]!r}, got {type(data["value"]).__name__!r}{src_info()}')

        else:
            if isinstance(data['value'], LingoPrimitiveTypes):
                value = data['value'].replace(r"\n", "\n").replace(r"\t", "\t") if data['type'] == 'str' else data['value']
                return symbols.L_SYM_value(
                    type=data['type'],
                    value=value,
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )
            elif data['type'] == 'list':
                if not isinstance(data['value'], list):
                    raise LingoSyntaxError(f'value type mismatch: expected list, got {type(data["value"]).__name__!r}{src_info()}')

                element_types = list(map(lambda x: type(x).__name__, data['value']))

                if len(set(element_types)) > 1:
                    raise LingoSyntaxError(f'value type mismatch: expected list of uniform types, got {element_types}{src_info()}')

                else:
                    return symbols.L_SYM_value(
                        type=data['type'],
                        value=data['value'],
                        element_type=element_types[0],
                        L_SRC=f'{L_SRC}.value',
                        L_FILE=ctx.interpreter.file,
                        L_LINE=get_yaml_line(data['value'])
                    )

            elif data['type'] == 'struct':
                if not isinstance(data['value'], dict):
                    raise LingoSyntaxError(f'value type mismatch: expected struct, got {type(data["value"]).__name__!r}{src_info()}')

                for key in data['value'].keys():
                    if not isinstance(key, str):
                        raise LingoSyntaxError(f'value type mismatch: expected struct with string keys, got key of type {type(key).__name__!r}{src_info()}')

                return symbols.L_SYM_value(
                    type=data['type'],
                    value=data['value'],
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )

            else:
                return symbols.L_SYM_value(
                    type=data['type'],
                    value=create_expression_ast(ctx, data['value'], f'{L_SRC}.value'),
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )

    elif keys == {'eq'}:
        return parse_expr_eq(ctx, data, L_SRC, src_info)

    elif 'int' in keys:
        return parse_expr_int(ctx, data, L_SRC, src_info)

    elif keys == {'add'}:
        return parse_expr_add(ctx, data, L_SRC, src_info)

    elif keys == {'str'}:
        return parse_expr_str(ctx, data, L_SRC)

    elif keys == {'concat'}:
        return parse_expr_concat(ctx, data, L_SRC, src_info)

    elif keys == {'join'}:
        return parse_expr_join(ctx, data, L_SRC, src_info)

    elif keys == {'break'}:
        if isinstance(data['break'], int) and (MIN_LINE_BREAKS <= data['break'] <= MAX_LINE_BREAKS):
            return symbols.L_SYM_break(
                        L_SRC=f'{L_SRC}.break',
                        breaks=data['break'],
                        L_FILE=ctx.interpreter.file,
                        L_LINE=get_yaml_line(data['break']),
                    )
        else:
            raise LingoSyntaxError(f'break must be int value between {MIN_LINE_BREAKS} and {MAX_LINE_BREAKS}, got: {data["break"]!r} at {src_info()}')

    elif 'heading' in keys:
        level = data.get('level', 1)
        if not isinstance(level, int) or not (MIN_HEADING_LEVEL <= level <= MAX_HEADING_LEVEL):
            raise LingoSyntaxError(f'heading level must be an int between {MIN_HEADING_LEVEL} and {MAX_HEADING_LEVEL}, got: {level!r} at {src_info()}')
        return symbols.L_SYM_heading(
            L_SRC=f'{L_SRC}.heading',
            text=create_expression_ast(ctx, data['heading'], f'{L_SRC}.heading.text'),
            level=level,
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['heading']),
        )

    elif 'link' in keys:
        try:
            text_expr = create_expression_ast(ctx, data['text'], f'{L_SRC}.text')
        except KeyError:
            text_expr = ''

        return symbols.L_SYM_link(
            L_SRC=f'{L_SRC}.link',
            link=create_expression_ast(ctx, data['link'], f'{L_SRC}.link'),
            text=text_expr,
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['link']),
        )
    elif 'text' in keys:
        try:
            style = LingoStyleOptions(**data['style']).validate()
        except KeyError:
            style = LingoStyleOptions()

        return symbols.L_SYM_text(
            L_SRC=f'{L_SRC}.text',
            text=create_expression_ast(ctx, data['text'], f'{L_SRC}.text'),
            style=style,
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['text']),
        )

    else:
        raise LingoSyntaxError(f'Unknown symbol: {", ".join(keys)}{src_info()}')

#
# symbol parsers
#

def parse_expr_eq(ctx, data: dict, L_SRC: str, src_info):
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


def parse_expr_int(ctx, data: dict, L_SRC: str, src_info):
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


def parse_expr_add(ctx, data: dict, L_SRC: str, src_info):
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

# str #


def parse_expr_str(ctx, data: dict, L_SRC: str):
    return symbols.L_SYM_str(
        object=create_expression_ast(ctx, data['str'], f'{L_SRC}.str.object'),
        L_SRC=f'{L_SRC}.str',
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(data['str'])
    )


def parse_expr_concat(ctx, data: dict, L_SRC: str, src_info):
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


def parse_expr_join(ctx, data: dict, L_SRC: str, src_info):
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
