from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from core.types import *
from core.util import *


__all__ = [
    'SingleModel'
]

# vars :: {"SingleModel": "model.name.pascal_case"}

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



field_list = [
    # replace :: macro.py_field_list(model.fields)
    'single_bool',
    'single_int',
    'single_float',
    'single_string',
    'single_enum',
    'single_datetime',
    # end replace ::
]

longest_field_name_length = max([len(name) for name in field_list])

@dataclass
class SingleModel:

    # replace :: macro.py_field_definitions(model.fields)
    single_bool: bool
    single_int: int
    single_float: float
    single_string: str
    single_enum: str
    single_datetime: datetime
    # end replace ::
    id: Optional[str] = None

    def convert_types(self) -> 'SingleModel':
        # insert :: macro.py_convert_types(model.fields)
        # macro :: py_convert_types_datetime :: {"single_datetime": "name"}
        # single_datetime - datetime
        if isinstance(self.single_datetime, str):
            self.single_datetime = datetime.strptime(self.single_datetime, datetime_format_str).replace(microsecond=0)
        # end macro ::
        return self

    def validate(self) -> 'SingleModel':
        
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
    def example(cls) -> 'SingleModel':
        return cls(
            # replace :: macro.py_example_fields(model.fields)
			single_bool=True,
			single_int=7,
			single_float=3.14,
			single_string='banana',
			single_enum='red',
			single_datetime=datetime.strptime('2000-01-11T12:34:56', datetime_format_str),
            # end replace ::
        ) 

    @classmethod
    def random(cls) -> 'SingleModel':
        return cls(
            # insert :: macro.py_random_fields(model.fields)
            # ignore ::
			single_bool=random_bool(),
			single_int=random_int(),
			single_float=random_float(),
			single_string=random_str(),
			single_enum=random_str_enum(single_enum_options),
			single_datetime=random_datetime(),
            # end ignore ::
        )