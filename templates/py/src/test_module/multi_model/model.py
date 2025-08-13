from core.types import *
from core.util import *

import json

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

__all__ = [
    'MultiModel'
]

# vars :: {"MultiModel": "model.name.pascal_case"}

# insert :: macro.py_enum_definitions(model.fields)
# macro :: py_enum_definition_begin :: {"single_enum": "field_name"}
single_enum_options = [
# macro :: py_enum_definition_option :: {"red": "option"}
    'red', 
# end macro ::
# ignore ::
    'green', 
    'blue',
# end ignore ::    
# macro :: py_enum_definition_end :: {}
]
# end macro ::

# ignore ::
multi_enum_options = [
    'giraffe', 
    'elephant', 
    'zebra'
]
# end ignore ::

field_list = [
    # replace :: macro.py_field_list(model.fields)
    'single_bool',
    'single_int',
    'single_float',
    'single_string',
    'single_enum',
    'single_datetime',
    'multi_bool',
    'multi_int',
    'multi_float',
    'multi_string',
    'multi_enum',
    'multi_datetime',
    # end replace ::
]

longest_field_name_length = max([len(name) for name in field_list])

@dataclass
class MultiModel:

    # replace :: macro.py_field_definitions(model.fields)
    single_bool: bool
    single_int: int
    single_float: float
    single_string: str
    single_enum: str
    single_datetime: datetime
    multi_bool: list[bool]
    multi_int: list[int]
    multi_float: list[float]
    multi_string: list[str]
    multi_enum: list[str]
    multi_datetime: list[datetime]
    # end replace ::
    id: Optional[str] = None

    def __post_init__(self):
        """post init"""
        # insert :: macro.py_post_init(model.fields)
        # macro :: py_post_init_datetime :: {"single_datetime": "name"}
        # single_datetime - datetime
        if isinstance(self.single_datetime, str):
            self.single_datetime = datetime.strptime(self.single_datetime, datetime_format_str).replace(microsecond=0)
        # end macro ::
        # macro :: py_post_init_list_datetime :: {"multi_datetime": "name"}
        # multi_datetime - list of datetime
        new_values = []
        for item in self.multi_datetime:
            if isinstance(item, str):
                new_values.append(datetime.strptime(item, datetime_format_str).replace(microsecond=0))
            else:
                new_values.append(item)
            
        self.multi_datetime = new_values
        # end macro ::

    def validate(self) -> 'MultiModel':

        if not isinstance(self.id, str) and self.id is not None:
            raise TypeError('invalid type for id')

        # insert :: macro.py_verify_fields(model.fields)

        # macro :: py_verify_bool :: {"single_bool": "name"}
        # single_bool - bool

        if not isinstance(self.single_bool, bool):
            raise TypeError('single_bool must be a bool')

        # macro :: py_verify_int :: {"single_int": "name"}
        # single_int - int

        if not isinstance(self.single_int, int):
            raise TypeError('single_int must be an integer')

        # macro :: py_verify_float :: {"single_float": "name"}
        # single_float - float

        if not isinstance(self.single_float, float):
            raise TypeError('single_float must be a float')

        # macro :: py_verify_str :: {"single_string": "name"}
        # single_string - str

        if not isinstance(self.single_string, str):
            raise TypeError('single_string must be a string')
        
        # macro :: py_verify_str_enum :: {"single_enum": "name"}
        # single_enum - str enum

        if self.single_enum not in single_enum_options:
            raise TypeError('invalid enum option for single_enum')

        # macro :: py_verify_datetime :: {"single_datetime": "name"}
        # single_datetime - datetime

        if not isinstance(self.single_datetime, datetime):
            raise TypeError('single_datetime must be a datetime')

        # macro :: py_verify_list_bool :: {"multi_bool": "name"}
        # multi_bool - list of bool

        if not isinstance(self.multi_bool, list):
            raise TypeError('multi_bool must be a list')
        
        for item in self.multi_bool:
            if not isinstance(item, bool):
                raise TypeError('multi_bool elements must be bool')

        # macro :: py_verify_list_int :: {"multi_int": "name"}
        # multi_int - list of int
   
        if not isinstance(self.multi_int, list):
            raise TypeError('multi_int must be a list')

        for item in self.multi_int:
            if not isinstance(item, int):
                raise TypeError('multi_int elements must be int')

        # macro :: py_verify_list_float :: {"multi_float": "name"}
        # multi_float - list of float

        if not isinstance(self.multi_float, list):
            raise TypeError('multi_float must be a list')
        
        for item in self.multi_float:
            if not isinstance(item, float):
                raise TypeError('multi_float elements must be float')

        # macro :: py_verify_list_str :: {"multi_string": "name"}
        # multi_string - list of str

        if not isinstance(self.multi_string, list):
            raise TypeError('multi_string must be a list')
        
        for item in self.multi_string:
            if not isinstance(item, str):
                raise TypeError('multi_string elements must be str')

        # macro :: py_verify_list_str_enum :: {"multi_enum": "name"}
        # multi_enum - list of str enum

        if not isinstance(self.multi_enum, list):
            raise TypeError('multi_enum must be a list')
        
        for item in self.multi_enum:
            if item not in multi_enum_options:
                raise TypeError('invalid enum option for multi_enum')
            
        # macro :: py_verify_list_datetime :: {"multi_datetime": "name"}
        # multi_datetime - list of datetime

        if not isinstance(self.multi_datetime, list):
            raise TypeError('multi_datetime must be a list')
        
        for item in self.multi_datetime:
            if not isinstance(item, datetime):
                raise TypeError('multi_datetime elements must be datetime')
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
    def from_json(cls, json_string:str) -> 'MultiModel':
        return cls(**json.loads(json_string))

    @classmethod
    def example(cls) -> 'MultiModel':
        return cls(
            # replace :: macro.py_example_fields(model.fields)
			single_bool=True,
			single_int=7,
			single_float=3.14,
			single_string='banana',
			single_enum='red',
			single_datetime=datetime.strptime('2000-01-11T12:34:56', datetime_format_str),
			multi_bool=[True, False],
			multi_int=[7, 11],
			multi_float=[3.14, 2.718],
			multi_string=['banana'],
            multi_enum=['giraffe', 'elephant'],
            multi_datetime=[datetime.strptime('2000-01-11T12:34:56', datetime_format_str)],
            # end replace ::
        ) 

    @classmethod
    def random(cls) -> 'MultiModel':
        return cls(
            # insert :: macro.py_random_fields(model.fields)
            # ignore ::
			single_bool=random_bool(),
			single_int=random_int(),
			single_float=random_float(),
			single_string=random_str(),
			single_enum=random_str_enum(single_enum_options),
			single_datetime=random_datetime(),
			multi_bool=random_list('bool'),
			multi_int=random_list('int'),
			multi_float=random_list('float'),
			multi_string=random_list('str'),
            multi_enum=random_list('str', multi_enum_options),
            multi_datetime=random_list('datetime'),
            # end ignore ::
        )