from dataclasses import dataclass
from typing import Any
import lingolib.symbols as symbols

from lingolib.context import LingoContext, LingoInterpreterContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoPrimitiveTypeNames, LingoPrimitiveTypes, LingoLiteralTypes, LingoScriptSpecs

import yaml

#####
#
#
# custom yaml parsing w/ line numbers
#
#
#####

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

#####
#
#
# lingo AST
#
#
#####


#
# definitions
#

@dataclass
class LingoASTExeSpec:
    lingo: symbols.L_SYM_lingo
    main: symbols.L_SYM_main

@dataclass
class LingoASTLibSpec:
    pass

LingoASTSpec = LingoASTExeSpec | LingoASTLibSpec

@dataclass
class LingoASTExpression:
    expression: symbols.ExpressionSymbols


#
# ast creation - specs
#


def create_spec_ast_from_dict(ctx: LingoContext, data: dict) -> LingoASTSpec:

    ctx.log.debug(f'create_spec_ast_from_dict')

    # parse lingo spec block #
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
        lingo:symbols.L_SYM_lingo = symbols.L_SYM_lingo(**lingo_args)
    except Exception as e:
        raise LingoSyntaxError(f'error creating lingo symbol: {e}')

    # delegate to spec-specific AST creation #

    if lingo.spec == 'exe':
        return spec_exe_ast_from_dict(ctx, lingo, data)
    else:
        raise LingoSyntaxError(f'unsupported lingo spec: {lingo.spec!r}')


def spec_exe_ast_from_dict(ctx: LingoContext, lingo: symbols.L_SYM_lingo, data: dict) -> LingoASTExeSpec:

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
        main:symbols.L_SYM_main = symbols.L_SYM_main(
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


#
# ast creation - reusables
#

"""

lingo AST

Build from yaml objects.

Example:

```yaml
type: int
value: 1
```

```yaml
add:
  a: 1
  b: 2
```

Each symbol corresponds to a symbol class in lingolib.symbols.

Root Keys
    Each symbol has root keys, which are the keys at the top level of the symbol dict.

    For the value symbol, the root keys are type and value. 

    For the add symbol, the root key is add.

Arg Keys
    The value symbol above does not have any arg keys

    The add symbol has arg keys a and b, which are the keys under the root key add.
    
"""


def create_expression_ast(ctx: LingoContext, data: LingoLiteralTypes, L_SRC: str) -> symbols.ExpressionSymbols:

    if isinstance(data, LingoPrimitiveTypes):
        ctx.log.debug(f'create_expression_ast - literal: {data!r}')
        return symbols.L_SYM_value(
            type=type(data).__name__, value=data, 
            L_SRC=f'{L_SRC}.literal',
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data)
        )

    elif isinstance(data, list):
        ctx.log.debug(f'create_expression_ast - list: {data!r}')
        return [create_expression_ast(ctx, item, f'{L_SRC}[{i}]') for i, item in enumerate(data)]
    
    elif isinstance(data, dict):
        return create_expression_ast_from_dict(ctx, data, L_SRC=L_SRC)
    
    else:
        raise LingoSyntaxError(f'unsupported expression type: {type(data).__name__!r}')
    

def create_expression_ast_from_dict(ctx: LingoContext, data: dict, L_SRC: str) -> symbols.ExpressionSymbols:

    keys = set(data.keys())
    ctx.log.debug(f'create_expression_ast_from_dict - keys: {keys!r}')

    line_no = get_yaml_line(data)

    def src_info():
        msg = f"; '{L_SRC}'"
        if ctx.interpreter.file:
            msg += f' in file {ctx.interpreter.file!r}'
            if line_no != -1:
                msg += f' at line {line_no}'
        return msg

    if keys == {'handle'}:
        return symbols.L_SYM_handle(
            expr=create_expression_ast(ctx, data['handle']), 
            L_SRC=f'{L_SRC}.handle',
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['handle'])
        )
    
    elif 'error' in keys:
        args = {
            'L_SRC': f'{L_SRC}.error', 
            'L_FILE': ctx.interpreter.file,
            'L_LINE': get_yaml_line(data)
        }
        for key in keys:
            match key:
                case 'error':
                    if isinstance(data['error'], str):
                        args['error'] = data['error']
                    else:
                        raise LingoSyntaxError(f'error field of error symbol must be a literal str value, expressions that return str are not supported{src_info()}')
                case 'code':
                    if isinstance(data['code'], str):
                        args['code'] = data['code']
                    else:
                        raise LingoSyntaxError(f'code field of error symbol must be a literal str value, expressions that return str are not supported{src_info()}')
                case _:
                    raise LingoSyntaxError(f'error symbol does not support key: {key!r}{src_info()}')
        return symbols.L_SYM_error(**args)

    elif keys == {'type', 'value'}:

        if data['type'] not in LingoPrimitiveTypeNames:
            raise LingoSyntaxError(f'invalid type for value symbol: {data["type"]!r}{src_info()}')
        
        elif isinstance(data['value'], LingoPrimitiveTypes) and type(data['value']).__name__ != data['type']:
            raise LingoSyntaxError(f'value type mismatch: expected {data["type"]!r}, got {type(data["value"]).__name__!r}{src_info()}')
        
        else:
            if isinstance(data['value'], LingoPrimitiveTypes):
                return symbols.L_SYM_value(
                    type=data['type'], 
                    value=data['value'], 
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )
            else:
                return symbols.L_SYM_value(
                    type=data['type'], 
                    value=create_expression_ast(ctx, data['value'], f'{L_SRC}.value'), 
                    L_SRC=f'{L_SRC}.value',
                    L_FILE=ctx.interpreter.file,
                    L_LINE=get_yaml_line(data['value'])
                )

    # com

    elif keys == {'eq'}:
        try:
            a_expr = data['eq']['a']
            b_expr = data['eq']['b']
        except KeyError as e:
            raise LingoSyntaxError(f'eq symbol missing key: {e}{src_info()}') from None
        
        if len(keys) != 1:
            raise LingoSyntaxError(f'eq symbol does not support keys other than eq{src_info()}')
        else:
            return symbols.L_SYM_eq(
                a=create_expression_ast(ctx, a_expr, f'{L_SRC}.eq.a'),
                b=create_expression_ast(ctx, b_expr, f'{L_SRC}.eq.b'),
                L_SRC=f'{L_SRC}.eq',
                L_FILE=ctx.interpreter.file,
                L_LINE=get_yaml_line(data['eq'])
            )

    # int

    elif 'int' in keys:

        args = {
            'L_SRC': f'{L_SRC}.int', 
            'L_FILE': ctx.interpreter.file, 
            'L_LINE': get_yaml_line(data)
        }
        for key in keys:
            match key:
                case 'int':
                    args['number'] = create_expression_ast(ctx, data['int'], f'{L_SRC}.int.number')
                case 'base':
                    args['base'] = create_expression_ast(ctx, data['base'], f'{L_SRC}.int.base')
                case _:
                    raise LingoSyntaxError(f'int symbol does not support key: {key!r}{src_info()}')

        return symbols.L_SYM_int(**args)
    
    elif keys == {'add'}:
        try:
            a_expr = data['add']['a']
            b_expr = data['add']['b']
        except KeyError as e:
            raise LingoSyntaxError(f'add symbol missing arg key: {e}{src_info()}') from None
        
        if len(keys) != 1:
            raise LingoSyntaxError(f'add symbol does not support root keys other than add, got: {keys!r}{src_info()}')
        elif len(data['add'].keys()) != 2:
            raise LingoSyntaxError(f'add symbol requires exactly two arg keys: a and b, got: {list(data["add"].keys())!r}{src_info()}')
        else:
            return symbols.L_SYM_add(
                a=create_expression_ast(ctx, a_expr, f'{L_SRC}.add.a'),
                b=create_expression_ast(ctx, b_expr, f'{L_SRC}.add.b'),
                L_SRC=f'{L_SRC}.add',
                L_FILE=ctx.interpreter.file,
                L_LINE=get_yaml_line(data['add'])
            )
    
    # str

    elif keys == {'str'}:
        return symbols.L_SYM_str(
            object=create_expression_ast(ctx, data['str'], f'{L_SRC}.str.object'),
            L_SRC=f'{L_SRC}.str',
            L_FILE=ctx.interpreter.file,
            L_LINE=get_yaml_line(data['str'])
        )
        
    elif keys == {'concat'}:
        if isinstance(data['concat'], list):
            ctx.log.debug(f'create_expression_ast_from_dict - concat expression: {data["concat"]!r}')
            return symbols.L_SYM_concat(
                items=create_expression_ast(ctx, data['concat'], f'{L_SRC}.concat.items'),
                L_SRC=f'{L_SRC}.concat',
                L_FILE=ctx.interpreter.file,
                L_LINE=get_yaml_line(data['concat'])
            )
        else:
            raise LingoSyntaxError(f'concat symbol must have a list {src_info()}')
    
    else:
        
        raise LingoSyntaxError(f'Unknown symbol: {", ".join(keys)}{src_info()}')
    
#
# misc
#


def lingo_ast_to_string(spec: LingoASTSpec, indent=0):
    """
    recursively print a lingo AST spec in a human-readable format

    iterate over all attr pairs
        if the attr name starts w/ _ - skip (internal attr)
        if the attr value name starts with 'L_SYM' print it with indent
    """
    attr_names = filter(lambda name: not name.startswith('_') and not name.startswith('L_SYM'), dir(spec))
    output = []
    for name in attr_names:
        value = getattr(spec, name)
        if hasattr(value, 'L_SYM_NAME'):
            output.append('  ' * indent + f'L_SYM_{value.L_SYM_NAME}')
            output.append(lingo_ast_to_string(value, indent + 1))

        elif isinstance(value, list):
            output.append('  ' * indent + f'{name}:')
            for item in value:
                if hasattr(item, 'L_SYM_NAME'):
                    output.append('  ' * (indent + 1) + f'L_SYM_{item.L_SYM_NAME}')
                    output.append(lingo_ast_to_string(item, indent + 2))
                else:
                    output.append('  ' * (indent + 1) + f'{item!r}')
        elif isinstance(value, (str, int, float, bool)):
            output.append('  ' * indent + f'{name}: {value!r}')

    return '\n'.join(output)