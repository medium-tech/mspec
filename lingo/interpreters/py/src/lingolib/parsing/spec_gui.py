import lingolib.parsing.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from .ast import LingoASTGUISpec
from .state import get_yaml_line
from .expr import create_expression_ast


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

    return LingoASTGUISpec(lingo=lingo, block=block)
