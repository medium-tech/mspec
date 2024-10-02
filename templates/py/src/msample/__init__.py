import json
from copy import deepcopy

def to_json(data:dict, sort_keys=True, indent=4) -> str:
    return json.dumps(data, sort_keys=sort_keys, indent=indent)

def from_json(json_string:str) -> dict:
    return verify(json.loads(json_string))

def example() -> dict:
    return deepcopy({
        'name': 'this is a thing',
        'verified': True,
        'color': 'green',
        'age': 42,
        'score': 3.14,
        'tags': ['tag1', 'tag2', 'tag3']
    })

def verify(data:dict) -> dict:

    if not isinstance(data, dict):
        raise TypeError('input must be a dictionary')
    
    try:
        if not isinstance(data['id'], str):
            raise TypeError('id must be a string')
    except KeyError:
        pass

    try:
        if not isinstance(data['name'], str):
            raise TypeError('name must be a string')
    except KeyError:
        pass

    try:
        if not isinstance(data['verified'], bool):
            raise TypeError('verified must be a boolean')
    except KeyError:
        pass

    try:
        if not isinstance(data['color'], str):
            raise TypeError('color must be a string')
        if data['color'] not in ['red', 'green', 'blue']:
            raise TypeError('color must be one of: red, green, blue')
    except KeyError:
        pass

    try:
        if not isinstance(data['age'], int):
            raise TypeError('age must be an integer')
    except KeyError:
        pass

    try:
        if not isinstance(data['score'], float):
            raise TypeError('score must be a float')
    except KeyError:
        pass

    try:
        if not isinstance(data['tags'], list):
            raise TypeError('tags must be a list')
        for tag in data['tags']:
            if not isinstance(tag, str):
                raise TypeError('tags must be a list of strings')
    except KeyError:
        pass

    for key in data.keys():
        if key not in ['id', 'name', 'verified', 'color', 'age', 'score', 'tags']:
            raise KeyError(f'unknown key: {key}')

    return data
