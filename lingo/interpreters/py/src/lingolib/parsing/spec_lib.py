import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.parsing.shared import parse_define_symbol, parse_func_symbol

from ..ast import LingoASTLibSpec
from .state import get_yaml_line
from .spec_expression import create_expression_ast


def _parse_module_member(ctx: LingoContext, name: str, data: dict, L_SRC: str) -> symbols.L_SYM_define | symbols.L_SYM_value | symbols.L_SYM_func:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'module member {name!r} must be a mapping, got: {type(data).__name__!r}')

    keys = set(data.keys())

    if 'func' in keys:
        return parse_func_symbol(ctx, name, data)
    elif 'define' in keys:
        return parse_define_symbol(ctx, name, data, L_SRC)
    elif 'value' in keys:
        return create_expression_ast(ctx, data, L_SRC)
    else:
        raise LingoSyntaxError(f'module member {name!r} must contain one of: define, value, func')


def _parse_module_symbol(ctx: LingoContext, name: str, data: dict) -> symbols.L_SYM_module:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'module {name!r} must be a mapping, got: {type(data).__name__!r}')

    members = {
        member_name: _parse_module_member(ctx, member_name, member_data, f'modules.{name}.{member_name}')
        for member_name, member_data in data.items()
    }

    return symbols.L_SYM_module(
        L_SRC=f'modules.{name}',
        name=name,
        members=members,
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data)
    )


def _parse_modules_symbol(ctx: LingoContext, data: dict) -> symbols.L_SYM_modules:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'modules symbol must be a mapping, got: {type(data).__name__!r}')

    modules = {
        module_name: _parse_module_symbol(ctx, module_name, module_data)
        for module_name, module_data in data.items()
    }

    return symbols.L_SYM_modules(
        L_SRC='modules',
        members=modules,
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data)
    )


def spec_lib_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict,
) -> LingoASTLibSpec:

    ctx.log.debug('spec_lib_ast_from_dict')

    try:
        modules_data = data['modules']
    except KeyError:
        raise LingoSyntaxError('missing modules symbol') from None

    modules_symbol = _parse_modules_symbol(ctx, modules_data)

    return LingoASTLibSpec(
        lingo=lingo,
        modules=modules_symbol,
    )
