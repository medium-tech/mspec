import json
from dataclasses import asdict
from datetime import datetime
from core.types import *
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
    return to_json(data, sort_keys=sort_keys, indent=indent)

def example_item_from_json(json_string:str) -> dict:
    return example_item_verify(json.loads(json_string))

def example_item_example() -> dict:
    return {
        # replace :: macro.py_example_fields(model.fields)
        'description': 'a large thing',
        'verified': True,
        'color': 'red',
        'count': 36,
        'score': 7.3,
        'tags': ['tag1', 'tag2'],
        'ids': ['05P9jRI5j4Or3oeQG4X_C0r56fL41d5G1bo1wdsI0XJw334.json', '05P9jRI5j4Or3oeQG4X_C0r56fL41d5G1bo1wdsI0XJw334.json'],
        'item': '05P9jRI5j4Or3oeQG4X_C0r56fL41d5G1bo1wdsI0XJw334.json',
        'meta': meta(),
        'when': datetime.now(),
        'admin': entity('05P9jRI5j4Or3oeQG4X_C0r56fL41d5G1bo1wdsI0XJw334.json', 'user'),
        'perms': permission(read='public', write='public', delete='public'),
        # end replace ::
    }

def example_item_random() -> dict:
    return {
        # insert :: macro.py_random_fields(model.fields)
        # macro :: py_random_str :: {"description": "field"}
        'description': random_str(),
        # macro :: py_random_bool :: {"verified": "field"}
        'verified': random_bool(),
        # macro :: py_random_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
        'color': random_enum(['red', 'green', 'blue']),
        # macro :: py_random_int :: {"count": "field"}
        'count': random_int(),
        # macro :: py_random_float :: {"score": "field"}
        'score': random_float(),
        # macro :: py_random_list :: {"tags": "field", "str": "element_type"}
        'tags': random_list('str'),
        # end macro ::
        'ids': random_list('cid'),
        # macro :: py_random_cid :: {"item": "field"}
        'item': random_cid(),
        # macro :: pyrandom_meta :: {"meta": "field"}
        'meta': meta(),
        # macro :: py_random_datetime :: {"when": "field"}
        'when': random_datetime(),
        # macro :: py_random_entity :: {"admin": "field"}
        'admin': random_entity(),
        # macro :: py_random_permission :: {"perms": "field"}
        'perms': random_permission(),
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

    # macro :: py_verify_str :: {"description": "field"}
    try:
        if not isinstance(data['description'], str):
            raise TypeError('description must be a string')
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

    # macro :: py_verify_int :: {"count": "field"}
    try:
        if not isinstance(data['count'], int):
            raise TypeError('count must be an integer')
    except KeyError:
        pass

    # macro :: py_verify_float :: {"score": "field"}
    try:
        if not isinstance(data['score'], float):
            raise TypeError('score must be a float')
    except KeyError:
        pass

    # macro :: py_verify_list :: {"tags": "field", "str": "element_type"}
    try:
        if not isinstance(data['tags'], list):
            raise TypeError('tags must be a list')
        for item in data['tags']:
            if not isinstance(item, str):
                raise TypeError('tag elements must be str')
            try:
                item.validate()
            except AttributeError:
                pass

    except KeyError:
        pass
    # end macro ::
    
    for key in data.keys():
        # vars :: {"['id', 'description', 'verified', 'color', 'count', 'score', 'tags']": "macro.py_field_list(model.fields)"}
        if key not in ['id', 'description', 'verified', 'color', 'count', 'score', 'tags']:
            raise KeyError(f'unknown key: {key}')

    return data
