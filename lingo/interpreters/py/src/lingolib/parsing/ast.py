from dataclasses import dataclass

import lingolib.parsing.symbols as symbols


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
