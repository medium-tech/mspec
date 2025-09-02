from core.types import *
from core.util import *

import json

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

__all__ = [
    'MultiModel'
]

multi_enum_options = [
    'giraffe', 
    'elephant', 
    'zebra'
]

field_list = [
    'multi_bool',
    'multi_int',
    'multi_float',
    'multi_string',
    'multi_enum',
    'multi_datetime',
    'user_id',
]

longest_field_name_length = max([len(name) for name in field_list])

@dataclass
class MultiModel:

    multi_bool: list[bool]
    multi_int: list[int]
    multi_float: list[float]
    multi_string: list[str]
    multi_enum: list[str]
    multi_datetime: list[datetime]
    user_id: str = ''
    id: Optional[str] = None

    def convert_types(self) -> 'MultiModel':
        # macro :: py_convert_types_list_datetime :: {"multi_datetime": "name"}
        # multi_datetime - list of datetime
        new_values = []
        for item in self.multi_datetime:
            if isinstance(item, str):
                new_values.append(datetime.strptime(item, datetime_format_str).replace(microsecond=0))
            else:
                new_values.append(item)
            
        self.multi_datetime = new_values
        # end macro ::
        return self

    def validate(self) -> 'MultiModel':

        if not isinstance(self.id, str) and self.id is not None:
            raise TypeError('invalid type for id')

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
    def example(cls) -> 'MultiModel':
        return cls(
			multi_bool=[True, False],
			multi_int=[7, 11],
			multi_float=[3.14, 2.718],
			multi_string=['banana'],
            multi_enum=['giraffe', 'elephant'],
            multi_datetime=[datetime.strptime('2000-01-11T12:34:56', datetime_format_str)],
        ) 

    @classmethod
    def random(cls) -> 'MultiModel':
        return cls(
			multi_bool=random_list('bool'),
			multi_int=random_list('int'),
			multi_float=random_list('float'),
			multi_string=random_list('str'),
            multi_enum=random_list('str', multi_enum_options),
            multi_datetime=random_list('datetime'),
        )