import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoScriptSpecs

from .ast import LingoASTSpec
from .expr_entry import create_expression_ast
from .spec_exe import spec_exe_ast_from_dict
from .state import get_yaml_line


def create_spec_ast_from_dict(ctx: LingoContext, data: dict) -> LingoASTSpec:

    ctx.log.debug(f'create_spec_ast_from_dict')

    lingo_args = {
        'L_SRC': 'lingo',
        'L_FILE': ctx.interpreter.file,
        'L_LINE': get_yaml_line(data)
    }
    for lingo_key, value in data['lingo'].items():
        match lingo_key:
            case 'spec':
                if value not in LingoScriptSpecs:
                    raise LingoSyntaxError(f'invalid lingo spec: {value!r}')
                elif not isinstance(value, str):
                    raise LingoSyntaxError(f'lingo spec must be a string literal, got: {type(value).__name__!r}')
                else:
                    lingo_args['spec'] = value
            case 'version':
                if not isinstance(value, str):
                    raise LingoSyntaxError(f'lingo version must be a string literal, got: {type(value).__name__!r}')
                else:
                    lingo_args['version'] = value
            case _:
                raise LingoSyntaxError(f'unsupported key in lingo symbol: {lingo_key!r}')

    try:
        lingo: symbols.L_SYM_lingo = symbols.L_SYM_lingo(**lingo_args)
    except Exception as e:
        raise LingoSyntaxError(f'error creating lingo symbol: {e}')

    if lingo.spec == 'exe':
        return spec_exe_ast_from_dict(
            ctx=ctx,
            lingo=lingo,
            data=data,
            create_expression_ast=create_expression_ast,
        )

    raise LingoSyntaxError(f'unsupported lingo spec: {lingo.spec!r}')
