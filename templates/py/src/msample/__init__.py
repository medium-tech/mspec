import json
import random
from copy import deepcopy

def to_json(data:dict, sort_keys=True, indent=4) -> str:
    return json.dumps(data, sort_keys=sort_keys, indent=indent)

def from_json(json_string:str) -> dict:
    return verify(json.loads(json_string))

name_examples = ['a large thing', 'a random thing', 'another thing']
verified_examples = [True, False]
color_examples = ['red', 'green', 'blue']
age_examples = [36, 27, 42]
score_examples = [4.7, 8.1, 9.9]
tags_examples = [['tag1', 'tag2'], ['tag3', 'tag4'], ['tag5', 'tag6']]

def random_sample_item() -> dict:
    return {
        'name': random.choice(name_examples),
        'verified': random.choice(verified_examples),
        'color': random.choice(color_examples),
        'age': random.choice(age_examples),
        'score': random.choice(score_examples),
        'tags': random.choice(tags_examples)
    }

def example_sample_item() -> dict:
    return {
        'name': name_examples[0],
        'verified': verified_examples[0],
        'color': color_examples[0],
        'age': age_examples[0],
        'score': score_examples[0],
        'tags': tags_examples[0]
    }

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
