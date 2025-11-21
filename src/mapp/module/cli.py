import importlib
from mapp.module.model import cli as model_cli

def add_module_subparser(subparsers, module_name, module_spec):
    module_parser = subparsers.add_parser(module_name, help=f"Module: {module_name}")
    model_subparsers = module_parser.add_subparsers(dest="model", required=True)
    for model_name, model in module_spec.get("models", {}).items():
        model_cli.add_model_subparser(model_subparsers, model_name, model)
