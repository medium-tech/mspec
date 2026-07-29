import lingolib.parsing.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from .ast import LingoASTExeSpec
from .state import get_yaml_line
from .expr import create_expression_ast


def spec_exe_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict,
) -> LingoASTExeSpec:

    ctx.log.debug(f'spec_exe_ast_from_dict')

    try:
        main_dict = data['main']
    except KeyError:
        raise LingoSyntaxError('missing main symbol')

    try:
        main_expr = create_expression_ast(ctx, main_dict, 'main')
    except LingoSyntaxError:
        raise
    except Exception as e:
        raise LingoSyntaxError(f'error creating main expression AST: {e.__class__.__name__}: {e}')

    try:
        main: symbols.L_SYM_main = symbols.L_SYM_main(
            L_SRC='main',
            expr=main_expr,
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(main_dict)
        )
    except KeyError:
        raise LingoSyntaxError('missing main symbol')
    except Exception as e:
        raise LingoSyntaxError(f'error creating main symbol: {e}')

    return LingoASTExeSpec(lingo=lingo, main=main)
