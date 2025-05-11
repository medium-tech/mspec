from core.types import *
from core.util import *

import json

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

__all__ = [
    'TestModel'
]

# vars :: {"TestModel": "model.name.pascal_case"}


@dataclass
class TestModel:

    # replace :: macro.py_field_definitions(model.fields)
    # end replace ::
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

    id: Optional[str] = None

    def __post_init__(self):
        """post init"""
        # insert :: macro.py_post_init(model.fields)
        # single_datetime - datetime
        if isinstance(self.single_datetime, str):
            self.single_datetime = datetime.strptime(self.single_datetime, datetime_format_str).replace(microsecond=0)
        elif isinstance(self.single_datetime, datetime):
            self.single_datetime = self.single_datetime.replace(microsecond=0)


        # macro :: py_post_init_datetime :: {"when": "name"}
        # end macro ::

    def validate(self) -> 'TestModel':
        
        try:
            if not isinstance(self.id, str) and self.id is not None:
                raise TypeError('invalid type for id')
        except KeyError:
            pass

        # insert :: macro.py_verify_fields(model.fields)
        # single_bool - bool
        try:
            if not isinstance(self.single_bool, bool):
                raise TypeError('single_bool must be a boolean')
        except KeyError:
            pass
        

        # single_int - int
        try:
            if not isinstance(self.single_int, int):
                raise TypeError('single_int must be an integer')
        except KeyError:
            pass


        # single_float - float
        try:
            if not isinstance(self.single_float, float):
                raise TypeError('single_float must be a float')
        except KeyError:
            pass


        # single_string - str
        try:
            if not isinstance(self.single_string, str):
                raise TypeError('single_string must be a string')
        except KeyError:
            pass
        

        # single_enum - str enum
        try:
            if not isinstance(self.single_enum, str):
                raise TypeError('single_enum must be a string')
            if self.single_enum not in ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']:
                raise TypeError('invalid choice for single_enum')
        except KeyError:
            pass


        # single_datetime - datetime
        try:
            if not isinstance(self.single_datetime, datetime):
                raise TypeError('single_datetime must be a datetime')
        except KeyError:
            pass
        

        # multi_bool - list of bool
        try:
            if not isinstance(self.multi_bool, list):
                raise TypeError('multi_bool must be a list')
            for item in self.multi_bool:
                if not isinstance(item, bool):
                    raise TypeError('multi_bool elements must be bool')

        except KeyError:
            pass


        # multi_int - list of int
        try:
            if not isinstance(self.multi_int, list):
                raise TypeError('multi_int must be a list')
            for item in self.multi_int:
                if not isinstance(item, int):
                    raise TypeError('multi_int elements must be int')

        except KeyError:
            pass


        # multi_float - list of float
        try:
            if not isinstance(self.multi_float, list):
                raise TypeError('multi_float must be a list')
            for item in self.multi_float:
                if not isinstance(item, float):
                    raise TypeError('multi_float elements must be float')

        except KeyError:
            pass


        # multi_string - list of str
        try:
            if not isinstance(self.multi_string, list):
                raise TypeError('multi_string must be a list')
            for item in self.multi_string:
                if not isinstance(item, str):
                    raise TypeError('multi_string elements must be str')

        except KeyError:
            pass




        # macro :: py_verify_str :: {"description": "name"}
        # macro :: py_verify_bool :: {"verified": "name"}
        # macro :: py_verify_str_enum :: {"color": "name", "['red', 'green', 'blue']": "enum_value_list"}
        # macro :: py_verify_int :: {"count": "name"}
        # macro :: py_verify_float :: {"score": "name"}
        # macro :: py_verify_list :: {"stuff": "name", "str": "element_type"}
        # macro :: py_verify_datetime :: {"when": "name"}
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
    def from_json(cls, json_string:str) -> 'TestModel':
        return cls(**json.loads(json_string))

    @classmethod
    def example(cls) -> 'TestModel':
        return cls(
            # replace :: macro.py_example_fields(model.fields)
            # end replace ::
			single_bool=True,
			single_int=7,
			single_float=3.14,
			single_string='banana',
			single_enum='red',
			single_datetime=datetime.strptime('2000-01-11T12:34:56.000000', '%Y-%m-%dT%H:%M:%S.%f'),
			multi_bool=[True, False],
			multi_int=[7, 11],
			multi_float=[3.14, 2.718],
			multi_string=['banana']
        ) 

    @classmethod
    def random(cls) -> 'TestModel':
        return cls(
            # insert :: macro.py_random_fields(model.fields)
			single_bool=random_bool(),
			single_int=random_int(),
			single_float=random_float(),
			single_string=random_str(),
			single_enum=random_enum(['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']),
			single_datetime=random_datetime(),
			multi_bool=random_list('bool'),
			multi_int=random_list('int'),
			multi_float=random_list('float'),
			multi_string=random_list('str')
            # macro :: py_random_str :: {"description": "field"}
            # macro :: py_random_bool :: {"verified": "field"}
            # macro :: py_random_enum :: {"color": "field", "['red', 'green', 'blue']": "enum_value_list"}
            # macro :: py_random_int :: {"count": "field"}
            # macro :: py_random_float :: {"score": "field"}
            # macro :: py_random_list :: {"tags": "field", "str": "element_type"}
            # macro :: py_random_datetime :: {"when": "field"}
            # end macro ::
        )