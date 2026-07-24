import lingolib.symbols as symbols

from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoPrimitiveTypeNames, LingoPrimitiveTypes

from .expr_numeric import parse_expr_add, parse_expr_eq, parse_expr_int
from .expr_text import parse_expr_concat, parse_expr_join, parse_expr_str


def parse_expression_ast_from_dict(ctx, data: dict, L_SRC: str, create_expression_ast, get_yaml_line):
    keys = set(data.keys())
    ctx.log.debug(f'create_expression_ast_from_dict - keys: {keys!r}')

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

    elif keys == {'type', 'value'}:

        if data['type'] not in LingoPrimitiveTypeNames:
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
            else:
                return symbols.L_SYM_value(
                    type=data['type'],
                    value=create_expression_ast(ctx, data['value'], f'{L_SRC}.value'),
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )

    elif keys == {'eq'}:
        return parse_expr_eq(ctx, data, L_SRC, create_expression_ast, get_yaml_line, src_info)

    elif 'int' in keys:
        return parse_expr_int(ctx, data, L_SRC, create_expression_ast, get_yaml_line, src_info)

    elif keys == {'add'}:
        return parse_expr_add(ctx, data, L_SRC, create_expression_ast, get_yaml_line, src_info)

    elif keys == {'str'}:
        return parse_expr_str(ctx, data, L_SRC, create_expression_ast, get_yaml_line)

    elif keys == {'concat'}:
        return parse_expr_concat(ctx, data, L_SRC, create_expression_ast, get_yaml_line, src_info)

    elif keys == {'join'}:
        return parse_expr_join(ctx, data, L_SRC, create_expression_ast, get_yaml_line, src_info)

    else:
        raise LingoSyntaxError(f'Unknown symbol: {", ".join(keys)}{src_info()}')
