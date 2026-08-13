from lingolib.parsing.spec_core import parse_define_symbol, parse_func_symbol
import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from ..ast import LingoASTGUISpec
from .state import get_yaml_line
from .expr import create_expression_ast


def _parse_state_symbol(ctx: LingoContext, data: dict) -> symbols.L_SYM_state:
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
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data)
    )


def _parse_ops_symbol(ctx: LingoContext, data: dict) -> symbols.L_SYM_ops:
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
        L_FILE=ctx.parser.file,
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
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(block_data),
    )

    state_symbol = _parse_state_symbol(ctx, data.get('state', dict()))
    ops_symbol = _parse_ops_symbol(ctx, data.get('ops', dict()))
    return LingoASTGUISpec(lingo=lingo, block=block, state=state_symbol, ops=ops_symbol)
