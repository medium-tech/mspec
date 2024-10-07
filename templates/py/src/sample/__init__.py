import json
from core import *
from sample.db import *

__all__ = [
    'seed_data',
    # for :: {% for model in module.models %} :: {"sample_item": "model.snake_case"}
    'sample_item_to_json',
    'sample_item_from_json',
    'sample_item_example',
    'sample_item_random',
    'sample_item_verify',
    # end for ::
]

def seed_data(count:int=100):
    for _ in range(count):
        # for :: {% for model in module.models %} :: {"sample_item": "model.snake_case"}
        db_create_sample_item(sample_item_random())
        # end for ::

# for :: {% for model in module.models %} :: {"sample_item": "model.snake_case", "SampleItem": "model.pascal_case"}
def sample_item_to_json(data:dict, sort_keys=True, indent=4) -> str:
    return json.dumps(data, sort_keys=sort_keys, indent=indent)

def sample_item_from_json(json_string:str) -> dict:
    return sample_item_verify(json.loads(json_string))

def sample_item_example() -> dict:
    return {
        # replace :: model.python_example_fields
        'name': 'a large thing',
        'verified': True,
        'color': 'red',
        'age': 36,
        'score': 7.3,
        'tags': ['tag1', 'tag2']
        # end replace ::
    }

def sample_item_random() -> dict:
    return {
        # replace :: model.python_random_fields
        # macro :: python_random_string :: {"name": "macro.arg.field"}
        'name': random_string(),
        # macro :: python_random_bool :: {"verified": "macro.arg.field"}
        'verified': random_bool(),
        # macro :: python_random_enum :: {"color": "macro.arg.field", "['red', 'green', 'blue']": "macro.arg.enum_value_list"}
        'color': random_enum(['red', 'green', 'blue']),
        # macro :: python_random_int :: {"age": "macro.arg.field"}
        'age': random_int(),
        # macro :: python_random_float :: {"score": "macro.arg.field"}
        'score': random_float(),
        # macro :: python_random_list :: {"tags": "macro.arg.field"}
        'tags': random_list()
        # end replace ::
    }

def sample_item_verify(data:dict) -> dict:

    if not isinstance(data, dict):
        raise TypeError('data must be a dictionary')
    
    try:
        if not isinstance(data['id'], str):
            raise TypeError('id must be a string')
    except KeyError:
        pass

    # replace :: model.python_verify_fields

    # macro :: python_verify_string :: {"name": "macro.arg.field"}
    try:
        if not isinstance(data['name'], str):
            raise TypeError('name must be a string')
    except KeyError:
        pass
    
    # macro :: python_verify_bool :: {"verified": "macro.arg.field"}
    try:
        if not isinstance(data['verified'], bool):
            raise TypeError('verified must be a boolean')
    except KeyError:
        pass
    
    # macro :: python_verify_enum :: {"color": "macro.arg.field", "['red', 'green', 'blue']": "macro.arg.enum_value_list"}
    try:
        if not isinstance(data['color'], str):
            raise TypeError('color must be a string')
        if data['color'] not in ['red', 'green', 'blue']:
            raise TypeError('invalid choice for color')
    except KeyError:
        pass

    # macro :: python_verify_int :: {"age": "macro.arg.field"}
    try:
        if not isinstance(data['age'], int):
            raise TypeError('age must be an integer')
    except KeyError:
        pass

    # macro :: python_verify_float :: {"score": "macro.arg.field"}
    try:
        if not isinstance(data['score'], float):
            raise TypeError('score must be a float')
    except KeyError:
        pass

    # macro :: python_verify_list :: {"tags": "macro.arg.field"}
    try:
        if not isinstance(data['tags'], list):
            raise TypeError('tags must be a list')
        for tag in data['tags']:
            if not isinstance(tag, str):
                raise TypeError('tags must be a list of strings')
    except KeyError:
        pass

    # end replace ::
    
    for key in data.keys():
        # vars :: {"['id', 'name', 'verified', 'color', 'age', 'score', 'tags']": "model.python_field_list"}
        if key not in ['id', 'name', 'verified', 'color', 'age', 'score', 'tags']:
            raise KeyError(f'unknown key: {key}')

    return data
# end for ::