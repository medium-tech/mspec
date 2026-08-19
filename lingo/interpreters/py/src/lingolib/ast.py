from dataclasses import dataclass

from lingolib.types import LingoStyleOptions, LingoListDisplayOptions
import lingolib.symbols as symbols


@dataclass
class LingoASTExeSpec:
    lingo: symbols.L_SYM_lingo
    main: symbols.L_SYM_main
    imports: symbols.L_SYM_imports | None = None
    params: symbols.L_SYM_params | None = None

@dataclass
class LingoASTAppSpec:
    pass

@dataclass
class LingoASTGUISpec:
    lingo: symbols.L_SYM_lingo
    block: symbols.L_SYM_block
    state: symbols.L_SYM_state | None = None
    ops: symbols.L_SYM_ops | None = None
    params: symbols.L_SYM_params | None = None

@dataclass
class LingoASTTextSpec:
    lingo: symbols.L_SYM_lingo
    block: symbols.L_SYM_block

@dataclass
class LingoASTLibSpec:
    lingo: symbols.L_SYM_lingo
    modules: symbols.L_SYM_modules


LingoASTSpec = LingoASTExeSpec | LingoASTLibSpec | LingoASTAppSpec | LingoASTGUISpec | LingoASTTextSpec


@dataclass
class LingoASTExpression:
    expression: symbols.ExpressionSymbols


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
        elif isinstance(value, dict):
            output.append('  ' * indent + f'{name}:')
            for key, item in value.items():
                if hasattr(item, 'L_SYM_NAME'):
                    output.append('  ' * (indent + 1) + f'{key}:')
                    output.append('  ' * (indent + 2) + f'L_SYM_{item.L_SYM_NAME}')
                    output.append(lingo_ast_to_string(item, indent + 3))
                else:
                    output.append('  ' * (indent + 1) + f'{key}: {item!r}')
        elif isinstance(value, (str, int, float, bool)):
            output.append('  ' * indent + f'{name}: {value!r}')

        elif isinstance(value, (LingoStyleOptions, LingoListDisplayOptions)):
            output.append('  ' * indent + f'{name}: {value!r}')

    return '\n'.join(output)
