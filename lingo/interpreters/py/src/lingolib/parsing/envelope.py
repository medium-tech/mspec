import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoScriptSpecs

from .ast import LingoASTSpec
from .expr_entry import create_expression_ast
from .spec_exe import spec_exe_ast_from_dict
from .state import get_yaml_line


SPEC_ROOT_RULES = {
    'exe': {
        'required': {'lingo', 'main'},
        'optional': {'meta', 'import'},
    },
    'lib': {
        'required': {'lingo', 'modules'},
        'optional': {'meta'},
    },
    'app': {
        'required': {'lingo', 'modules'},
        'optional': {'meta', 'import'},
    },
    'ui': {
        'required': {'lingo', 'state', 'ops', 'output'},
        'optional': {'meta', 'backend', 'import'},
    },
}


def validate_spec_root(spec_name: str, doc: dict) -> None:
    rules = SPEC_ROOT_RULES.get(spec_name)
    if rules is None:
        raise LingoSyntaxError(f'no root rules registered for spec: {spec_name!r}')

    top_level_keys = set(doc.keys())
    required_keys = rules['required']
    optional_keys = rules['optional']

    missing_required = required_keys - top_level_keys
    if missing_required:
        raise LingoSyntaxError(
            f'missing required top-level key(s) for spec {spec_name!r}: '
            f'{", ".join(sorted(missing_required))}'
        )

    allowed_keys = required_keys | optional_keys
    unknown_keys = top_level_keys - allowed_keys
    if unknown_keys:
        raise LingoSyntaxError(
            f'unsupported top-level key(s) for spec {spec_name!r}: '
            f'{", ".join(sorted(unknown_keys))}; '
            f'allowed: {", ".join(sorted(allowed_keys))}'
        )


def create_spec_ast_from_dict(ctx: LingoContext, data: dict) -> LingoASTSpec:

    ctx.log.debug(f'create_spec_ast_from_dict')

    if not isinstance(data, dict):
        raise LingoSyntaxError(f'spec document must be a mapping, got: {type(data).__name__!r}')

    if 'lingo' not in data:
        raise LingoSyntaxError('missing required top-level key for all specs: lingo')

    if not isinstance(data['lingo'], dict):
        raise LingoSyntaxError(f'lingo symbol must be a mapping, got: {type(data["lingo"]).__name__!r}')

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

    validate_spec_root(lingo.spec, data)

    if lingo.spec == 'exe':
        return spec_exe_ast_from_dict(
            ctx=ctx,
            lingo=lingo,
            data=data,
            create_expression_ast=create_expression_ast,
        )

    raise LingoSyntaxError(f'spec {lingo.spec!r} passed root validation, but AST parser is not implemented yet')
