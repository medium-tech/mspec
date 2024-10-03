import json
import random
from copy import deepcopy

def to_json(data:dict, sort_keys=True, indent=4) -> str:
    return json.dumps(data, sort_keys=sort_keys, indent=indent)

def from_json(json_string:str) -> dict:
    return verify(json.loads(json_string))

_random_nouns = ['apple', 'banana', 'horse', 'iguana', 'jellyfish', 'kangaroo', 'lion', 'quail', 'rabbit', 'snake', 'tiger', 'x-ray', 'yak', 'zebra']
_random_adjectives = ['shiny', 'dull', 'new', 'old', 'big', 'small', 'fast', 'slow', 'hot', 'cold', 'happy', 'sad', 'angry', 'calm', 'loud', 'quiet']
_random_words = _random_nouns + _random_adjectives

def random_sample_item() -> dict:
    num = random.randint(1, 4)
    if num == 1:
        name = random.choice(_random_adjectives) + ' ' + random.choice(_random_nouns)
    elif num == 2:
        name = ('The ' + random.choice(_random_nouns) + ' ' + random.choice(_random_nouns)).title()
    elif num == 3:
        name = random.choice(_random_words).title()
        if random.randint(0, 2) == 0:
            name += f'_{random.randint(1, 100)}'
    elif num == 4:
        _words = []
        
        for i in range(random.randint(3, 4)):
            _word = random.choice(_random_words)
            if random.randint(0, 2) == 0:
                _words.append(_word.upper())
            else:
                _words.append(_word)

        random.shuffle(_words)
        name = ' '.join(_words)

    return {
        'name': name,
        'verified': bool(random.randint(0, 1)),
        'color': random.choice(['red', 'green', 'blue']),
        'age': random.randint(1, 100),
        'score': round(random.random() * random.randint(1, 15), 1),
        'tags': random.choices(_random_adjectives, k=random.randint(1, 3))
    }

def example_sample_item() -> dict:
    return {
        'name': 'a large thing',
        'verified': True,
        'color': 'red',
        'age': 36,
        'score': 7.3,
        'tags': ['tag1', 'tag2']
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
