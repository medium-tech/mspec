from mapp.errors import MappError
from mapp.module.model import cli as model_cli

def add_module_subparser(subparsers, module_spec):

    # init module cli #

    module_kebab_case = module_spec['name']['kebab_case']

    module_parser = subparsers.add_parser(module_kebab_case, help=f'Module: {module_kebab_case}')
    model_subparsers = module_parser.add_subparsers(dest='model', required=False)

    help_parser = model_subparsers.add_parser('help', help='Show help for this module', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda args: module_parser.print_help())

    # parsers for each model #

    try:
        spec_models = module_spec['models']
    except KeyError:
        raise MappError('NO_MODELS_DEFINED', f'No models defined in module: {module_kebab_case}')

    for model in spec_models.values():
        model_cli.add_model_subparser(model_subparsers, model)

