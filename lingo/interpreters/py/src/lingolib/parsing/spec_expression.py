from copy import deepcopy

from lingolib.constants import (
    MIN_LINE_BREAKS,
    MAX_LINE_BREAKS,
    MIN_HEADING_LEVEL,
    MAX_HEADING_LEVEL,
)
import lingolib.symbols as symbols


from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
import lingolib.symbols as symbols
from lingolib.types import (
    LingoLiteralTypeNames, 
    LingoLanguageError, 
    LingoLiteralTypes, 
    LingoPrimitiveTypes, 
    LingoStyleOptions, 
    LingoListDisplayOptions,
    PythonTypeNamesToLingoTypes
)


from .state import get_yaml_line


def create_expression_ast(
    ctx: LingoContext,
    data: LingoLiteralTypes,
    L_SRC: str,
) -> symbols.ExpressionSymbols:

    if isinstance(data, LingoPrimitiveTypes):
        # ctx.log.debug(f'create_expression_ast - literal: {data!r}')
        type_name = type(data).__name__
        value = data.replace(r'\n', '\n').replace(r'\t', '\t') if type_name == 'str' else data
        try:
            l_file = ctx.parser.file
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
        # ctx.log.debug(f'create_expression_ast - error: {data!r}')
        try:
            l_file = ctx.parser.file
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
        # ctx.log.debug(f'create_expression_ast - list: {data!r}')
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


def parse_expression_ast_from_dict(ctx, data: dict, L_SRC: str):
    keys = set(data.keys())
    # ctx.log.debug(f'parse_expression_ast_from_dict - keys: {keys!r}')

    line_no = get_yaml_line(data)

    def src_info():
        msg = f"; '{L_SRC}'"
        if ctx.parser.file:
            msg += f' in file {ctx.parser.file!r}'
            if line_no != -1:
                msg += f' at line {line_no}'
        return msg

    if keys == {'handle'}:
        return symbols.L_SYM_handle(
            L_SRC=f'{L_SRC}.handle',
            expr=create_expression_ast(ctx, data['handle'], f'{L_SRC}.handle.expr'),
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data['handle'])
        )

    elif 'error' in keys:
        args = {
            'L_SRC': f'{L_SRC}.error',
            'L_FILE': ctx.parser.file,
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
                    L_FILE=ctx.parser.file,
                    L_LINE=get_yaml_line(data['value'])
                )
            
            elif data['type'] == 'list':
                if not isinstance(data['value'], list):
                    raise LingoSyntaxError(f'value type mismatch: expected list, got {type(data["value"]).__name__!r}{src_info()}')

                try:
                    element_type = data['element_type']
                except KeyError as e:
                    ctx.log.debug(f'create_expression_ast_from_dict - list element type not specified, attempting to infer from first element: {data["value"]!r}')
                    try:
                        py_element_type = type(data['value'][0]).__name__
                        
                    except IndexError as e:
                        raise LingoSyntaxError(f'could not determine element type for empty list, supply with "element_type" key in value symbol: {e}{src_info()}') from None

                    try:
                        element_type = PythonTypeNamesToLingoTypes[py_element_type]
                    except KeyError as e:
                        raise LingoSyntaxError(f'unsupported element type for list: {py_element_type!r}{src_info()}') from None
                
                display = LingoListDisplayOptions.from_dict(data.get('display', {}))

                if display.format == 'table':
                    if element_type != 'struct':
                        raise LingoSyntaxError(f'list display format "table" requires element_type "struct", got: {element_type!r}{src_info()}')

                if element_type == 'struct':
                    parsed_elements = []
                    for i, item in enumerate(data['value']):
                        if not isinstance(item, dict):
                            raise LingoSyntaxError(f'value type mismatch: expected list of struct, got element of type {type(item).__name__!r} at index {i}{src_info()}')
                        
                        elif 'type' in item:
                            if item['type'] != 'struct':
                                raise LingoSyntaxError(f'value type mismatch: expected list of struct, got element of type {item["type"]!r} at index {i}{src_info()}')
                            else:
                                parsed_elements.append(create_expression_ast(ctx, item, f'{L_SRC}.value[{i}]'))
                        else:
                            wrapped_struct = {'type': 'struct', 'value': deepcopy(item)}
                            parsed_elements.append(create_expression_ast(ctx, wrapped_struct, f'{L_SRC}.value[{i}]'))
                else:
                    parsed_elements = [create_expression_ast(ctx, item, f'{L_SRC}.value[{i}]') for i, item in enumerate(data['value'])]

                return symbols.L_SYM_value(
                    type=data['type'],
                    value=parsed_elements,
                    element_type=element_type,
                    display=display,
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.parser.file,
                    L_LINE=get_yaml_line(data['value'])
                )

            elif data['type'] == 'struct':
                # breakpoint()
                if not isinstance(data['value'], dict):
                    raise LingoSyntaxError(f'value type mismatch: expected struct, got {type(data["value"]).__name__!r}{src_info()}')

                for key in data['value'].keys():
                    if not isinstance(key, str):
                        raise LingoSyntaxError(f'value type mismatch: expected struct with string keys, got key of type {type(key).__name__!r}{src_info()}')

                return symbols.L_SYM_value(
                    type=data['type'],
                    value=data['value'],
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.parser.file,
                    L_LINE=get_yaml_line(data['value'])
                )

            else:
                
                return symbols.L_SYM_value(
                    type=data['type'],
                    value=create_expression_ast(ctx, data['value'], f'{L_SRC}.value'),
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.parser.file,
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

    elif keys == {'get'}:
        return parse_expr_get(ctx, data, L_SRC, src_info)

    elif keys == {'validate'}:
        return parse_expr_validate(ctx, data, L_SRC, src_info)

    elif 'call' in keys:
        return parse_expr_call(ctx, data, L_SRC, src_info)

    elif keys == {'args'}:
        return parse_expr_args(ctx, data, L_SRC, src_info)

    elif keys == {'set', 'to'}:
        return parse_expr_set(ctx, data, L_SRC, src_info)

    elif keys == {'break'}:
        if isinstance(data['break'], int) and (MIN_LINE_BREAKS <= data['break'] <= MAX_LINE_BREAKS):
            return symbols.L_SYM_break(
                        L_SRC=f'{L_SRC}.break',
                        breaks=data['break'],
                        L_FILE=ctx.parser.file,
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
            L_FILE=ctx.parser.file,
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
            L_FILE=ctx.parser.file,
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
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data['text']),
        )

    elif 'button' in keys:
        try:
            call_str = data['button']['call']
            text_expr = data['button']['text']
        except KeyError as e:
            breakpoint()
            raise LingoSyntaxError(f'button symbol missing required key: {e}{src_info()}')
        
        if not isinstance(call_str, str):
            raise LingoSyntaxError(f'button call must be a string literal, got: {type(call_str).__name__!r}{src_info()}')

        text_expr = create_expression_ast(ctx, text_expr, f'{L_SRC}.button.text')

        return symbols.L_SYM_button(
            L_SRC=f'{L_SRC}.button',
            call=call_str,
            text=text_expr,
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data['button']),
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
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['eq'])
    )


def parse_expr_int(ctx, data: dict, L_SRC: str, src_info):
    keys = set(data.keys())
    args = {
        'L_SRC': f'{L_SRC}.int',
        'L_FILE': ctx.parser.file,
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
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['add'])
    )

# str #


def parse_expr_str(ctx, data: dict, L_SRC: str):
    return symbols.L_SYM_str(
        object=create_expression_ast(ctx, data['str'], f'{L_SRC}.str.object'),
        L_SRC=f'{L_SRC}.str',
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['str'])
    )


def parse_expr_concat(ctx, data: dict, L_SRC: str, src_info):
    if isinstance(data['concat'], list):
        ctx.log.debug(f'create_expression_ast_from_dict - concat expression: {data["concat"]!r}')
        return symbols.L_SYM_concat(
            items=create_expression_ast(ctx, data['concat'], f'{L_SRC}.concat.items'),
            L_SRC=f'{L_SRC}.concat',
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data['concat'])
        )
    else:
        raise LingoSyntaxError(f'concat symbol must have a list {src_info()}')


def parse_expr_join(ctx, data: dict, L_SRC: str, src_info):
    ctx.log.debug(f'create_expression_ast_from_dict - join expression: {data}')
    args = {
        'L_SRC': f'{L_SRC}.join',
        'L_FILE': ctx.parser.file,
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


def parse_expr_get(ctx, data: dict, L_SRC: str, src_info):

    get_data = data['get']

    if isinstance(get_data, str):
        parts = get_data.split('.')
        if len(parts) != 2:
            raise LingoSyntaxError(f'get symbol shorthand must be in the form data_source.field_name, got: {get_data!r}{src_info()}')

        from_str, field_name = parts

        return symbols.L_SYM_get(
            field=field_name,
            from_=create_expression_ast(ctx, from_str, f'{L_SRC}.get.from'),
            L_SRC=f'{L_SRC}.get',
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(get_data)
        )

    elif isinstance(get_data, dict):
        get_keys = set(get_data.keys())
        if get_keys != {'field', 'from'}:
            raise LingoSyntaxError(f'get field mapping requires exactly "field" and "from" keys, got: {", ".join(sorted(get_keys))}{src_info()}')

        if not isinstance(get_data['field'], str):
            raise LingoSyntaxError(f'get field name must be a string, got: {type(get_data["field"]).__name__!r}{src_info()}')

        return symbols.L_SYM_get(
            field=get_data['field'],
            from_=create_expression_ast(ctx, get_data['from'], f'{L_SRC}.get.from'),
            L_SRC=f'{L_SRC}.get',
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(get_data)
        )

    else:
        raise LingoSyntaxError(f'get symbol requires a string path or a field/from mapping, got: {type(get_data).__name__!r}{src_info()}')


def parse_expr_validate(ctx, data: dict, L_SRC: str, src_info):
    # deferred import to avoid a circular import with shared.py, which imports create_expression_ast from this module
    from lingolib.parsing.shared import parse_define_symbol

    validate_data = data['validate']
    if not isinstance(validate_data, dict):
        raise LingoSyntaxError(f'validate symbol requires a mapping, got: {type(validate_data).__name__!r}{src_info()}')

    try:
        item_data = validate_data['item']
    except KeyError:
        raise LingoSyntaxError(f'validate symbol missing required key: item{src_info()}') from None

    try:
        against_data = validate_data['against']
    except KeyError:
        raise LingoSyntaxError(f'validate symbol missing required key: against{src_info()}') from None

    unsupported = set(validate_data.keys()) - {'item', 'against'}
    if unsupported:
        raise LingoSyntaxError(f'unsupported key(s) in validate symbol: {", ".join(sorted(unsupported))}{src_info()}')

    item_expr = create_expression_ast(ctx, item_data, f'{L_SRC}.validate.item')

    if isinstance(against_data, str):
        against = against_data
    elif isinstance(against_data, dict):
        against = parse_define_symbol(ctx, 'against', against_data, f'{L_SRC}.validate.against')
    else:
        raise LingoSyntaxError(f'validate against must be a string reference or a define mapping, got: {type(against_data).__name__!r}{src_info()}')

    return symbols.L_SYM_validate(
        item=item_expr,
        against=against,
        L_SRC=f'{L_SRC}.validate',
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(validate_data)
    )


def parse_expr_call(ctx, data: dict, L_SRC: str, src_info):

    unsupported = set(data.keys()) - {'call', 'args'}
    if unsupported:
        raise LingoSyntaxError(f'unsupported key(s) in call symbol: {", ".join(sorted(unsupported))}{src_info()}')

    if not isinstance(data['call'], str):
        raise LingoSyntaxError(f'call symbol requires a string function reference, got: {type(data["call"]).__name__!r}{src_info()}')

    args_data = data.get('args', {})
    if not isinstance(args_data, dict):
        raise LingoSyntaxError(f'call args must be a mapping, got: {type(args_data).__name__!r}{src_info()}')

    args = {
        arg_name: create_expression_ast(ctx, arg_data, f'{L_SRC}.call.args.{arg_name}')
        for arg_name, arg_data in args_data.items()
    }

    return symbols.L_SYM_call(
        func=data['call'],
        args=args,
        L_SRC=f'{L_SRC}.call',
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['call'])
    )


def parse_expr_set(ctx, data: dict, L_SRC: str, src_info):

    if not isinstance(data['set'], str):
        raise LingoSyntaxError(f'set symbol requires a string path, got: {type(data["set"]).__name__!r}{src_info()}')

    return symbols.L_SYM_set(
        name=data['set'],
        value=create_expression_ast(ctx, data['to'], f'{L_SRC}.set.to'),
        L_SRC=f'{L_SRC}.set',
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['set'])
    )


def parse_expr_args(ctx, data: dict, L_SRC: str, src_info):

    if not isinstance(data['args'], str):
        raise LingoSyntaxError(f'args symbol requires a string name, got: {type(data["args"]).__name__!r}{src_info()}')

    return symbols.L_SYM_args(
        name=data['args'],
        L_SRC=f'{L_SRC}.args',
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data['args'])
    )
