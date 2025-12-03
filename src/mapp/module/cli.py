from mapp.errors import MappError
from mapp.module.model.cli import add_model_subparser
from mapp.module.op.cli import add_op_subparser


__all__ = [
    'add_module_subparser'
]

def add_module_subparser(subparsers, spec:dict, module:dict):

    # init module cli #
    project_name = spec['project']['name']['kebab_case']
    module_kebab_case = module['name']['kebab_case']
    description = f':: {project_name} :: {module_kebab_case}'

    module_parser = subparsers.add_parser(module_kebab_case, help=f'Module: {module_kebab_case}', description=description)
    model_subparsers = module_parser.add_subparsers(dest='model', required=False)

    help_parser = model_subparsers.add_parser('help', help='Show help for this module', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda ctx, args: module_parser.print_help())

    # parsers for each model #

    for model in module.get('models', {}).values():
        if model.get('hidden', False) is True:
            continue
        add_model_subparser(model_subparsers, spec, module, model)

    # parsers for each op #

    for op in module.get('ops', {}).values():
        if op.get('hidden', False) is True:
            continue
        add_op_subparser(model_subparsers, spec, module, op)
