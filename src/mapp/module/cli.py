from mapp.module.model import cli as model_cli

def add_module_subparser(subparsers, module_spec):
    module_kebab_case = module_spec['name']['kebab_case']

    module_parser = subparsers.add_parser(module_kebab_case, help=f'Module: {module_kebab_case}')
    model_subparsers = module_parser.add_subparsers(dest='model', required=True)

    for model in module_spec.get('models', {}).values():
        model_cli.add_model_subparser(model_subparsers, model)
