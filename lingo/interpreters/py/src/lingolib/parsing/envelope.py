from typing import Any

import lingolib.symbols as symbols
import yaml

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoScriptSpecs

from .ast import LingoASTSpec
from .spec_exe import spec_exe_ast_from_dict


class YamlLocationLoader(yaml.SafeLoader):
    pass


YamlLocationLoader.anchors = {}


def get_yaml_line(obj: Any) -> int:
    return YamlLocationLoader.anchors.get(id(obj), -1)


def construct_mapping_with_locations(loader, node):
    loader.flatten_mapping(node)
    mapping = loader.construct_mapping(node)
    # Map the object ID to its start line (1-indexed)
    YamlLocationLoader.anchors[id(mapping)] = node.start_mark.line + 1
    return mapping


def construct_sequence_with_locations(loader, node):
    seq = loader.construct_sequence(node)
    # Map the list ID to its start line
    YamlLocationLoader.anchors[id(seq)] = node.start_mark.line + 1
    return seq


def construct_scalar_with_locations(loader, node):
    val = loader.construct_scalar(node)
    # Map the string/int/bool ID to its start line
    YamlLocationLoader.anchors[id(val)] = node.start_mark.line + 1
    return val


YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping_with_locations
)
YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    construct_sequence_with_locations
)
YamlLocationLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    construct_scalar_with_locations
)


def create_spec_ast_from_dict(
    ctx: LingoContext,
    data: dict,
    create_expression_ast,
    get_yaml_line,
) -> LingoASTSpec:

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
            get_yaml_line=get_yaml_line,
        )

    raise LingoSyntaxError(f'unsupported lingo spec: {lingo.spec!r}')
