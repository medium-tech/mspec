def http_model_create(model_class:type, model:object) -> object:
    print('[PLACEHOLDER] Would create a single model via HTTP API.')

def http_model_read(model_class: type, model_id: str) -> object:
    print(f'[PLACEHOLDER] Would read model with id={model_id} via HTTP API.')

def http_model_update(model_class: type, model_id: str, model: object) -> object:
    print(f'[PLACEHOLDER] Would update model with id={model_id} via HTTP API.')

def http_model_delete(model_class: type, model_id: str):
    print(f'[PLACEHOLDER] Would delete model with id={model_id} via HTTP API.')

def http_model_list(model_class: type, offset: int = 0, limit: int = 50) -> dict:
    print(f'[PLACEHOLDER] Would list models via HTTP API with offset={offset} and limit={limit}.')
