import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError

from lingolib.ast import LingoASTAppSpec
from lingolib.parsing.shared import parse_define_symbol, parse_func_symbol, parse_imports_symbol
from lingolib.parsing.state import get_yaml_line


def _parse_app_op(ctx: LingoContext, name: str, data: object, L_SRC: str) -> symbols.L_SYM_func:
    if isinstance(data, str):
        if not data:
            raise LingoSyntaxError(f'op reference for {name!r} must not be empty')
        return symbols.L_SYM_func(
            L_SRC=L_SRC,
            name=name,
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data),
            reference=data,
        )
    else:
        return parse_func_symbol(ctx, name, data, L_SRC=L_SRC)


def _parse_app_model(ctx: LingoContext, name: str, data: object, L_SRC: str) -> symbols.L_SYM_define:
    if isinstance(data, dict) and 'model' in data:
        if set(data) != {'model'}:
            raise LingoSyntaxError(f'model reference for {name!r} cannot contain additional keys')
        reference = data['model']
        if not isinstance(reference, str):
            raise LingoSyntaxError(f'model reference for {name!r} must be a string, got: {type(reference).__name__!r}')
        if not reference:
            raise LingoSyntaxError(f'model reference for {name!r} must not be empty')
        return symbols.L_SYM_define(
            L_SRC=L_SRC,
            name=name,
            type=None,
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(data),
            reference=reference,
        )
    else:
        return parse_define_symbol(ctx, name, data, L_SRC)


def _parse_app_module(ctx: LingoContext, name: str, data: object) -> symbols.L_SYM_app_module:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'app module {name!r} must be a mapping, got: {type(data).__name__!r}')

    unsupported = set(data) - {'ops', 'models'}
    if unsupported:
        raise LingoSyntaxError(
            f'unsupported key(s) in app module {name!r}: {", ".join(sorted(unsupported))}'
        )

    ops_data = data.get('ops', {})
    if not isinstance(ops_data, dict):
        raise LingoSyntaxError(
            f'ops in app module {name!r} must be a mapping, got: {type(ops_data).__name__!r}'
        )
    ops = {}
    for op_name, op_data in ops_data.items():
        if not isinstance(op_name, str):
            raise LingoSyntaxError(f'ops names in app module {name!r} must be strings')
        ops[op_name] = _parse_app_op(
            ctx, op_name, op_data, f'modules.{name}.ops.{op_name}'
        )

    models_data = data.get('models', {})
    if not isinstance(models_data, dict):
        raise LingoSyntaxError(
            f'models in app module {name!r} must be a mapping, got: {type(models_data).__name__!r}'
        )
    models = {}
    for model_name, model_data in models_data.items():
        if not isinstance(model_name, str):
            raise LingoSyntaxError(f'model names in app module {name!r} must be strings')
        models[model_name] = _parse_app_model(
            ctx, model_name, model_data, f'modules.{name}.models.{model_name}'
        )

    return symbols.L_SYM_app_module(
        L_SRC=f'modules.{name}',
        name=name,
        ops=symbols.L_SYM_ops(
            L_SRC=f'modules.{name}.ops',
            funcs=ops,
            L_FILE=ctx.parser.file,
            L_LINE=get_yaml_line(ops_data),
        ),
        models=models,
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data),
    )


def _parse_app_modules(ctx: LingoContext, data: object) -> symbols.L_SYM_app_modules:
    if not isinstance(data, dict):
        raise LingoSyntaxError(f'modules symbol must be a mapping, got: {type(data).__name__!r}')

    for module_name in data:
        if not isinstance(module_name, str):
            raise LingoSyntaxError('app module names must be strings')

    modules = {
        module_name: _parse_app_module(ctx, module_name, module_data)
        for module_name, module_data in data.items()
    }
    return symbols.L_SYM_app_modules(
        L_SRC='modules',
        members=modules,
        L_FILE=ctx.parser.file,
        L_LINE=get_yaml_line(data),
    )


def spec_app_ast_from_dict(
    ctx: LingoContext,
    lingo: symbols.L_SYM_lingo,
    data: dict,
) -> LingoASTAppSpec:
    ctx.log.debug('spec_app_ast_from_dict')

    modules = _parse_app_modules(ctx, data['modules'])
    imports = parse_imports_symbol(ctx, data.get('imports', []))
    return LingoASTAppSpec(lingo=lingo, modules=modules, imports=imports)