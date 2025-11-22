def db_model_create_table(model_class: type):
    print('[PLACEHOLDER] Would create the table for the model in the local SQLite database.')

def db_model_create(model_class: type, data: dict):
    print('[PLACEHOLDER] Would create a single model in the local SQLite database.')

def db_model_read(model_class: type, model_id: str):
    print(f'[PLACEHOLDER] Would read model with id={model_id} from the local SQLite database.')

def db_model_update(model_class: type, model_id: str, data: dict):
    print(f'[PLACEHOLDER] Would update model with id={model_id} in the local SQLite database.')

def db_model_delete(model_class: type, model_id: str):
    print(f'[PLACEHOLDER] Would delete model with id={model_id} from the local SQLite database.')

def db_model_list(model_class: type, offset: int = 0, limit: int = 50):
    print(f'[PLACEHOLDER] Would list models from the local SQLite database with offset={offset} and limit={limit}.')
