from core.types import *
from core.util import *

import json

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

__all__ = [
    'ExampleItem'
]

# vars :: {"ExampleItem": "model.name.pascal_case"}


@dataclass
class ExampleItem:

    # replace :: macro.py_field_definitions(model.fields)
    description: str
    verified: bool
    color: str
    count: int
    score: float
    stuff: list[str]
    when: datetime
    # end replace ::
    id: Optional[str] = None

    def __post_init__(self):
        # lower resolution of datetime for mongo compatibility
        if isinstance(self.when, str):
            dt, millis = self.when.split('.')
            new_ts = f'{dt}.{millis[0:3]}'
            
        else:
            dt, millis = self.when.strftime(iso_format_str).split('.')
            new_ts = f'{dt}.{millis[0:3]}'
        
        self.when = datetime.strptime(new_ts, iso_format_str)

    def validate(self) -> 'ExampleItem':
        
        try:
            if not isinstance(self.id, str) and self.id is not None:
                raise TypeError('invalid type for id')
        except KeyError:
            pass

        # insert :: macro.py_verify_fields(model.fields)

        # macro :: py_verify_str :: {"description": "field.name"}
        try:
            if not isinstance(self.description, str):
                raise TypeError('description must be a string')
        except KeyError:
            pass
        
        # macro :: py_verify_bool :: {"verified": "field"}
        try:
            if not isinstance(self.verified, bool):
                raise TypeError('verified must be a boolean')
        except KeyError:
            pass
        
        # macro :: py_verify_str_enum :: {"color": "field.name", "['red', 'green', 'blue']": "field.enum_value_list"}
        try:
            if not isinstance(self.color, str):
                raise TypeError('color must be a string')
            if self.color not in ['red', 'green', 'blue']:
                raise TypeError('invalid choice for color')
        except KeyError:
            pass

        # macro :: py_verify_int :: {"count": "field.name"}
        try:
            if not isinstance(self.count, int):
                raise TypeError('count must be an integer')
        except KeyError:
            pass

        # macro :: py_verify_float :: {"score": "field.name"}
        try:
            if not isinstance(self.score, float):
                raise TypeError('score must be a float')
        except KeyError:
            pass

        # macro :: py_verify_list :: {"stuff": "field.name", "str": "field.element_type"}
        try:
            if not isinstance(self.stuff, list):
                raise TypeError('stuff must be a list')
            for item in self.stuff:
                if not isinstance(item, str):
                    raise TypeError('stuff elements must be str')

        except KeyError:
            pass

        # macro :: py_verify_datetime :: {"stuff": "field.name"}
        try:
            if not isinstance(self.when, datetime):
                raise TypeError('when must be a datetime')
        except KeyError:
            pass
        
        # end macro ::
        
        return self   

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.id is None:
            del data['id']
        return data
    
    def to_json(self) -> str:
        return to_json(self.to_dict())
    
    @classmethod
    def from_json(cls, json_string:str) -> 'ExampleItem':
        return cls(**json.loads(json_string))

    @classmethod
    def example(cls) -> 'ExampleItem':
        return cls(
            description='a large thing',
            verified=True,
            color='red',
            count=36,
            score=7.3,
            stuff=['apple', 'banana', 'pear'],
            when=datetime.now()
        ) 

    @classmethod
    def random(cls) -> 'ExampleItem':
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
            'stuff': random_list('str'),
            # macro :: py_random_datetime :: {"when": "field"}
            'when': random_datetime(),
            # end macro ::
        }
