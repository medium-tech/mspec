import lingolib.parsing.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoLanguageError, LingoLiteralTypes, LingoPrimitiveTypes

from .expr_core import parse_expression_ast_from_dict
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
            create_expression_ast=create_expression_ast,
        )

    else:
        raise LingoSyntaxError(f'unsupported expression type: {type(data).__name__!r}')


def create_expression_ast_from_dict(
    ctx: LingoContext,
    data: dict,
    L_SRC: str,
    create_expression_ast,
) -> symbols.ExpressionSymbols:
    return parse_expression_ast_from_dict(
        ctx=ctx,
        data=data,
        L_SRC=L_SRC,
        create_expression_ast=create_expression_ast,
    )
