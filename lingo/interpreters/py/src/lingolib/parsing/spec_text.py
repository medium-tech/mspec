import lingolib.parsing.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from .ast import LingoASTTextSpec
from .state import get_yaml_line


def spec_text_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict,
    create_expression_ast,
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
        if not isinstance(item, dict):
            raise LingoSyntaxError(f'block item at index {index} must be a mapping, got: {type(item).__name__!r}')

        if 'text' not in item:
            raise LingoSyntaxError(f'block item at index {index} missing required key: text')

        text_expr = create_expression_ast(ctx, item['text'], f'block[{index}].text')
        block_items.append(
            symbols.L_SYM_text(
                L_SRC=f'block[{index}]',
                text=text_expr,
                L_FILE=ctx.interpreter.file,
                L_LINE=get_yaml_line(item),
            )
        )

    block = symbols.L_SYM_block(
        L_SRC='block',
        items=block_items,
        L_FILE=ctx.interpreter.file,
        L_LINE=get_yaml_line(block_data),
    )

    return LingoASTTextSpec(lingo=lingo, block=block)
