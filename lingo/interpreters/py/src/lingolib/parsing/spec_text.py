import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from ..ast import LingoASTTextSpec
from .state import get_yaml_line
from .spec_expression import create_expression_ast


def spec_text_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict
) -> LingoASTTextSpec:

    ctx.log.debug('spec_text_ast_from_dict')

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

    return LingoASTTextSpec(lingo=lingo, block=block)
