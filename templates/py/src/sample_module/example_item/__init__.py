import json
from core.util import *

__all__ = [
    'example_item_to_json',
    'example_item_from_json',
    'example_item_example',
    'example_item_random',
    'example_item_verify'
]

# vars :: {"example_item": "model.name.snake_case"}

def example_item_to_json(data:dict, sort_keys=True, indent=4) -> str:
    return json.dumps(data, sort_keys=sort_keys, indent=indent)

def example_item_from_json(json_string:str) -> dict:
    return example_item_verify(json.loads(json_string))

def example_item_example() -> dict:
    return {
        # replace :: macro.py_example_fields(model.fields)
        'name': 'a large thing',
        'verified': True,
        'color': 'red',
        'age': 36,
        'score': 7.3,
        'tags': ['tag1', 'tag2']
        # end replace ::
    }

def example_item_random() -> dict:
    return {
        # insert :: macro.py_random_fields(model.fields)
        # macro :: py_random_str :: {"name": "field"}
        'name': random_str(),
        # macro :: py_random_bool :: {"verified": "field"}
        'verified': random_bool(),
        # macro :: py_random_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
        'color': random_enum(['red', 'green', 'blue']),
        # macro :: py_random_int :: {"age": "field"}
        'age': random_int(),
        # macro :: py_random_float :: {"score": "field"}
        'score': random_float(),
        # macro :: py_random_list :: {"tags": "field"}
        'tags': random_list()
        # end macro ::
    }

def example_item_verify(data:dict) -> dict:

    if not isinstance(data, dict):
        raise TypeError('data must be a dictionary')
    
    try:
        if not isinstance(data['id'], str):
            raise TypeError('id must be a string')
    except KeyError:
        pass

    # insert :: macro.py_verify_fields(model.fields)

    # macro :: py_verify_str :: {"name": "field"}
    try:
        if not isinstance(data['name'], str):
            raise TypeError('name must be a string')
    except KeyError:
        pass
    
    # macro :: py_verify_bool :: {"verified": "field"}
    try:
        if not isinstance(data['verified'], bool):
            raise TypeError('verified must be a boolean')
    except KeyError:
        pass
    
    # macro :: py_verify_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
    try:
        if not isinstance(data['color'], str):
            raise TypeError('color must be a string')
        if data['color'] not in ['red', 'green', 'blue']:
            raise TypeError('invalid choice for color')
    except KeyError:
        pass

    # macro :: py_verify_int :: {"age": "field"}
    try:
        if not isinstance(data['age'], int):
            raise TypeError('age must be an integer')
    except KeyError:
        pass

    # macro :: py_verify_float :: {"score": "field"}
    try:
        if not isinstance(data['score'], float):
            raise TypeError('score must be a float')
    except KeyError:
        pass

    # macro :: py_verify_list :: {"tags": "field"}
    try:
        if not isinstance(data['tags'], list):
            raise TypeError('tags must be a list')
        for tag in data['tags']:
            if not isinstance(tag, str):
                raise TypeError('tags must be a list of strings')
    except KeyError:
        pass
    # end macro ::
    
    for key in data.keys():
        # vars :: {"['name', 'verified', 'color', 'age', 'score', 'tags']": "macro.py_field_list(model.fields)"}
        if key not in ['name', 'verified', 'color', 'age', 'score', 'tags']:
            raise KeyError(f'unknown key: {key}')

    return data
