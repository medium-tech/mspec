from mapp.context import MappContext
from mapp.errors import MappError
from mapp.types import new_model_class, Acknowledgment
from mapp.module.model.db import db_model_create_table

def create_tables(ctx: MappContext, spec: dict) -> Acknowledgment:
    try:
        spec_modules = spec['modules']
    except KeyError:
        raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

    for module in spec_modules.values():
        try:
            spec_models = module['models']
        except KeyError:
            raise MappError('NO_MODELS_DEFINED', f'No models defined in module: {module["name"]["kebab_case"]}')

        for model in spec_models.values():
            model_class = new_model_class(model, module)
            ack = db_model_create_table(ctx, model_class)
            if not isinstance(ack, Acknowledgment):
                raise MappError('TABLE_CREATION_FAILED', f'Failed to create table for model: {model_class._model_spec["name"]["kebab_case"]}')
    
    return Acknowledgment(message='All tables created or already existed.')
