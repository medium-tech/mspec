import json

from collections import namedtuple
from typing import Any, Optional, NamedTuple, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

from mapp.errors import MappValidationError, MappError

__all__ = [
    'DATETIME_FORMAT_STR',
    'Acknowledgment',
    'PlainTextResponse',
    'JSONResponse',
    'StaticFileResponse',

    'User',
    'UserSession',
    'PasswordHash',
    'CreateUserOutput',
    'LoginUserOutput',
    'CurrentUserOutput',
    'CurrentUserFuncReturn',
    'CurrentUserFunc',
    'CurrentAccessTokenFunc',

    'ModelListResult',
    'new_model_class',
    'new_model',
    'new_op_classes',
    'new_op_params',
    'new_op_output',
   
    'convert_dict_to_model',
    'convert_dict_to_op_params',

    'validate_model',
    'validate_op_params',
    'validate_op_output',

    'MappJsonEncoder',
    'model_to_json',
    'json_to_model',
    'json_to_model_w_convert',
    'model_list_from_json',
    'to_json',

    'json_to_op_params',
    'json_to_op_params_w_convert',
    'json_to_op_output',
    'op_output_to_json',
    'op_params_to_json',
    'redact_secure_fields'
]

#
# generics
#

DATETIME_FORMAT_STR = '%Y-%m-%dT%H:%M:%S'

class Acknowledgment:
    def __init__(self, message: str = 'No additional information') -> None:
        self.message = message
        self.acknowledged = True

    @classmethod
    def from_dict(cls, data: dict) -> 'Acknowledgment':
        if not data.get('acknowledged', False):
            raise ValueError('Acknowledgment data does not indicate success.')
        try:
            return cls(message=data['message'])
        except KeyError:
            raise ValueError('Acknowledgment data is missing required "message" field.')

    def to_dict(self) -> dict:
        if not self.acknowledged:
            raise ValueError('Acknowledgment instance does not indicate success.')
        return {
            'acknowledged': self.acknowledged,
            'message': self.message
        }

class PlainTextResponse(Exception):
    content_type = 'text/plain'
    def __init__(self, status:str, text:str) -> None:
        super().__init__('PlainTextResponse')
        self.status = status
        self.text = text

class JSONResponse(Exception):
    content_type = 'application/json'
    def __init__(self, status:str, data:dict|None=None) -> None:
        super().__init__('JSONResponse')
        self.status = status
        self.data = data

class StaticFileResponse(Exception):
    def __init__(self, status:str, content:bytes, content_type:str) -> None:
        super().__init__('StaticFileResponse')
        self.status = status
        self.content = content
        self.content_type = content_type

#
# auth
#

class User(NamedTuple):
    id: str
    name: str
    email: str

class UserSession(NamedTuple):
    id: str
    user_id: str
    created_at: datetime

class PasswordHash(NamedTuple):
    id: str
    user_id: str
    hash: str

class CreateUserOutput(NamedTuple):
    id: str
    name: str
    email: str

class LoginUserOutput(NamedTuple):
    access_token: str
    token_type: str

class CurrentUserOutput(NamedTuple):
    id: str
    name: str
    email: str
    number_of_sessions: int


CurrentUserFuncReturn = tuple[Optional[User], str]              # deprecated
CurrentUserFunc = Callable[[], Optional[CurrentUserFuncReturn]] # deprecated

CurrentAccessTokenFunc = Callable[[], Optional[str]]

#
# data
#

# class and instances #

@dataclass
class ModelListResult:
    items: list
    total: int

def new_model_class(model_spec:dict, module_spec:Optional[dict]=None) -> type:
    """
    Dynamically creates a model class based on the provided model specification.

    Args:
        model_spec (dict): The specification dictionary for the model.

    Returns:
        type: A dynamically created model class.
    """
    fields = ['id']
    try:
        class_name = model_spec['name']['pascal_case']
        fields += [field['name']['snake_case'] for field in model_spec['fields'].values()]
    except KeyError as e:
        raise ValueError(f'Missing required model specification key: {e}')
    
    new_class = namedtuple(class_name, fields)
    new_class._model_spec = model_spec
    new_class._module_spec = module_spec
    return new_class

def new_model(model_class:type, data:dict):
    """
    Creates an instance of the given model class using the provided data.

    No data type conversion is performed. Use convert_data_to_model for that.

    Args:
        model_class (type): The model class to instantiate.
        data (dict): A dictionary containing field values for the model.

    Returns:
        object: An instance of the model class.
    """

    if 'id' not in data:
        data['id'] = None

    try:
        return model_class(**data)
    except TypeError as e:
        raise ValueError(f'Error creating model instance: {e}')

def new_op_classes(op_spec:dict, module_spec:Optional[dict]=None) -> tuple[type, type]:
    """
    Dynamically creates a model class based on the provided model specification.

    Args:
        op_spec (dict): The specification dictionary for the op.

    Returns:
        tuple[type, type]: A tuple containing the dynamically created op params class and output class
            in that order.
    """

    # create params class #

    params_fields = []

    try:
        class_name = op_spec['name']['pascal_case']
        params_fields += [field['name']['snake_case'] for field in op_spec['params'].values()]
    except KeyError as e:
        raise ValueError(f'Missing required model specification key: {e}')
    
    params_class = namedtuple(f'{class_name}Params', params_fields)
    params_class._op_spec = op_spec
    params_class._module_spec = module_spec

    # create output class #

    output_fields = []

    try:
        output_fields += [field['name']['snake_case'] for field in op_spec['output'].values()]
    except KeyError as e:
        raise ValueError(f'Missing required model specification key: {e}')
    
    output_class = namedtuple(f'{class_name}Output', output_fields)
    output_class._op_spec = op_spec
    output_class._module_spec = module_spec

    return params_class, output_class

def new_op_params(op_class:type, data:dict):
    """
    Creates an instance of the given op class using the provided data.

    No data type conversion is performed. Use convert_data_to_model for that.

    Args:
        op_class (type): The op class to instantiate.
        data (dict): A dictionary containing field values for the op.

    Returns:
        object: An instance of the op param class.
    """

    try:
        return op_class(**data)
    except TypeError as e:
        raise ValueError(f'Error creating op instance: {e}')
    
def new_op_output(op_class:type, data:dict):
    """
    Creates an instance of the given op output class using the provided data.

    No data type conversion is performed. Use convert_data_to_model for that.

    Args:
        op_class (type): The op output class to instantiate.
        data (dict): A dictionary containing field values for the op output.

    Returns:
        object: An instance of the op output class.
    """

    try:
        return op_class(**data)
    except TypeError as e:
        raise ValueError(f'Error creating op output instance: {e}')

# conversion #

def _convert_incoming_value(field_type:str, raw_value:Any, strict=False) -> Any:
    """
    Converts a raw value to the specified field type.
    Args:
        field_type (str): The target field type as a string.
        raw_value (Any): The raw value to convert.
        strict (bool): Whether to enforce strict conversion for booleans.
            If strict is false, the following strings will be converted to bool:
            - True values: 'true', 't', '1', 'yes', 'on'
            - False values: 'false', 'f', '0', 'no', 'off
    Returns:
        Any: The converted value.
    Raises:
        ValueError: If the conversion fails or the field type is unsupported.
    """

    match field_type:
        case 'bool':
            if isinstance(raw_value, str):
                if not strict and raw_value.lower() in ('true', 't', '1', 'yes', 'on'):
                    return True
                elif not strict and raw_value.lower() in ('false', 'f', '0', 'no', 'off'):
                    return False
                else:
                    raise ValueError(f'Cannot convert string "{raw_value}" to bool')
            else:
                return bool(raw_value)
        case 'int':
            return int(raw_value)
        case 'float':
            return float(raw_value)
        case 'str':
            return str(raw_value)
        case 'datetime':
            if isinstance(raw_value, datetime):
                return raw_value
            elif isinstance(raw_value, str):
                return datetime.strptime(raw_value, DATETIME_FORMAT_STR)
            else:
                raise ValueError(f'Cannot convert type "{type(raw_value)}" to datetime')
        case 'foreign_key':
            return str(raw_value)
        case _:
            raise ValueError(f'Unsupported field type: {field_type}')

def _convert_incoming_fields(data_spec:dict, data:object) -> dict:

    converted_data = {}

    for field in data_spec.values():

        field_name = field['name']['snake_case']
        field_type = field['type']

        try:
            raw_value = data[field_name]
        except KeyError:
            """
            ignore this error, this function only converts provided fields,
            it does not validate the data
            """
            continue

        try:
            if isinstance(raw_value, list):
                converted_data[field_name] = [_convert_incoming_value(field['element_type'], v) for v in raw_value]
            else:
                converted_data[field_name] = _convert_incoming_value(field_type, raw_value)

        except (ValueError, TypeError) as e:
            raise ValueError(f'Error converting field "{field_name}" to type "{field_type}": {e}')

    return converted_data
     
def convert_dict_to_model(model_class:type, data:dict):
    """
    Converts a dictionary of data into an instance of the specified model class.

    Will convert types as necessary based on the model class definition.

    Useful for user input like CLI args.

    Args:
        model_class (type): The model class to instantiate.
        data (dict): A dictionary containing field values for the model.

    Returns:
        object: An instance of the model class.
    """

    converted_data = _convert_incoming_fields(model_class._model_spec['fields'], data)

    try:
        if isinstance(data['id'], str):
            converted_data['id'] = data['id']
        elif isinstance(data['id'], int):
            converted_data['id'] = str(data['id'])
        elif data['id'] is not None:
            raise ValueError('Model ID must be a string, int or None')
    except KeyError:
        pass

    return new_model(model_class, converted_data)

def convert_dict_to_op_params(op_class:type, data:dict):
    """
    Converts a dictionary of data into an instance of the specified op param class.

    Will convert types as necessary based on the op class definition.

    Useful for user input like CLI args.

    Args:
        op_class (type): The op param class to instantiate.
        data (dict): A dictionary containing field values for the op params.

    Returns:
        object: An instance of the op param class.
    """

    converted_data = _convert_incoming_fields(op_class._op_spec['params'], data)

    return new_op_params(op_class, converted_data)

# validation #

def _get_python_type_for_field(field_type:str) -> type:
    """
    Maps a field type string to the corresponding Python type.

    Args:
        field_type (str): The field type as a string.

    Returns:
        type: The corresponding Python type.

    Raises:
        ValueError: If the field type is unsupported.
    """

    match field_type:
        case 'bool':
            return bool
        case 'int':
            return int
        case 'float':
            return float
        case 'str':
            return str
        case 'datetime':
            return datetime
        case 'foreign_key':
            return str
        case _:
            raise ValueError(f'Unsupported field type: {field_type}')

def _validate_obj(data_spec:dict, obj_instance:object, err_msg:str) -> object:
    """
    Validates a model instance against its model class specification.

    Args:
        obj_class (type): The obj class to validate against.
        obj_instance (object): The obj instance to validate.
        
        
    Returns:
        The obj instance

    Raises:        
        MappValidationError: If the obj instance is invalid, containing a dictionary of error messages if any. 
            For any fields with validation errors, the dictionary will contain the field name as the key
            and the first error message for that field as the value.
    """

    errors = {}
    total_errors = 0

    for field in data_spec.values():

        # field definition #

        field_name = field['name']['snake_case']
        field_type = field['type']
        required = field.get('required', False)

        # get value #

        try:
            value = getattr(obj_instance, field_name)
        except AttributeError:
            if required:
                errors[field_name] = f'Field "{field_name}" is missing from the model instance.'
                total_errors += 1
            continue

        #
        # validate type
        #

        if field_type != 'list':

            # confirm value type #

            python_type = _get_python_type_for_field(field_type)

            if not isinstance(value, python_type):
                errors[field_name] = f'Field "{field_name}" is not of type "{field_type}".'
                total_errors += 1

        else:
            
            # confirm is list type #

            if not isinstance(value, list):
                errors[field_name] = f'Field "{field_name}" is expected to be a list.'
                total_errors += 1
                continue

            # element type definition #

            try:
                element_type = field['element_type']
            except KeyError:
                raise ValueError(f'Field "{field_name}" of type "list" is missing required "element_type".')
            
            python_type = _get_python_type_for_field(element_type)

            # confirm type of elements #

            for i, element in enumerate(value):
                if not isinstance(element, python_type):
                    errors[field_name] = f'Element {i} of field "{field_name}" is not "{element_type}".'
                    total_errors += 1
                    break

    if total_errors > 0:
        raise MappValidationError(err_msg, errors)
    
    return obj_instance

def validate_model(model_class:type, model_instance:object) -> object:
    return _validate_obj(
        model_class._model_spec['fields'], 
        model_instance,
        f'Model Validation failed for: {model_class._model_spec["name"]["pascal_case"]}'
    )

def validate_op_params(op_class:type, op_params_instance:object) -> object:
    return _validate_obj(
        op_class._op_spec['params'], 
        op_params_instance,
        f'Op Params Validation failed for: {op_class._op_spec["name"]["pascal_case"]}'
    )

def validate_op_output(op_class:type, op_output_instance:object) -> object:
    return _validate_obj(
        op_class._op_spec['output'], 
        op_output_instance,
        f'Op {op_class._op_spec["name"]["pascal_case"]} returned an invalid output'
    )

#
# json
#

class MappJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT_STR)
        elif isinstance(obj, ModelListResult):
            return {
                'items': [item._asdict() for item in obj.items],
                'total': obj.total
            }
        elif hasattr(obj, '_asdict'):
            return obj._asdict()
        elif isinstance(obj, Acknowledgment):
            return {
                'acknowledged': True,
                'message': obj.message
            }
        elif hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        else:
            return super().default(obj)

# model #

def model_to_json(obj:object, sort_keys=False, indent=None) -> str:
    try:
        return json.dumps(
            obj._asdict() if hasattr(obj, '_asdict') else obj,
            sort_keys=sort_keys, 
            indent=indent, 
            cls=MappJsonEncoder
        )
    except Exception as e:
        raise MappError('ERROR_SERIALIZING_TO_JSON', f'Error serializing to JSON: {e}')
    
def json_to_model(json_str:str, model_class:type, model_id:Optional[str]=None) -> object:
    try:
        data = json.loads(json_str)

        try:
            # if id is in both json and argument, they must match
            json_id = data['id']
            if model_id is not None and str(json_id) != str(model_id):
                raise ValueError('Model ID in JSON does not match the provided model_id argument.')
        except KeyError:
            # id provided as arg and not in json, set it
            if model_id is not None:
                data['id'] = model_id

        return new_model(model_class, data)
    
    except json.JSONDecodeError as e:
        raise MappValidationError(f'Invalid JSON: {e}')
    
    except TypeError as e:
        raise MappValidationError(f'Error creating model instance: {e}')
   
def json_to_model_w_convert(model_class:type, json_str:str, model_id:Optional[str]=None):
    """
    Converts a JSON string into an instance of the specified model class.

    Will convert types as necessary based on the model class definition.

    Id may be provided in the json or as a separate argument. It can also be omitted in both.

    If they are both provided they must match.

    Args:
        model_class (type): The model class to instantiate.
        json_str (str): A JSON string representing the model data.
        model_id (Optional[str]): An optional model ID to set on the instance.

    Returns:
        object: An instance of the model class.
    """

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f'Invalid JSON: {e}')
    
    json_id = data.get('id', None)

    # ensure ids match if both provided #
    if model_id is not None and json_id is not None:
            if str(json_id) != str(model_id):
                raise ValueError('Model ID in JSON does not match the provided model_id argument.')

    data['id'] = model_id

    return convert_dict_to_model(model_class, data)

def model_list_from_json(json_str:str, model_class:type) -> 'ModelListResult':
    try:
        data = json.loads(json_str)
        items = [model_class(**item) for item in data['items']]
        total = data['total']
        return ModelListResult(items=items, total=total)
    
    except json.JSONDecodeError as e:
        raise MappValidationError(f'Invalid JSON: {e}')
    
    except TypeError as e:
        raise MappValidationError(f'Error creating model instance: {e}')

to_json = model_to_json # alias for generic use

# op #

def json_to_op_params(json_str:str, op_class:type) -> object:
    try:
        data = json.loads(json_str)
        return new_op_params(op_class, data)
    except json.JSONDecodeError as e:
        raise MappValidationError(f'Invalid JSON: {e}')
    except TypeError as e:
        raise MappValidationError(f'Error creating op params instance: {e}')

def json_to_op_params_w_convert(json_str:str, op_class:type) -> object:
    """
    Converts a JSON string into an instance of the specified op param class.

    Will convert types as necessary based on the op class definition.

    Args:
        op_class (type): The op param class to instantiate.
        json_str (str): A JSON string representing the op param data.

    Returns:
        object: An instance of the op param class.
    """

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f'Invalid JSON: {e}')
    
    return convert_dict_to_op_params(op_class, data)

def json_to_op_output(json_str:str, op_class:type) -> object:
    try:
        data = json.loads(json_str)
        return new_op_output(op_class, data)
    except json.JSONDecodeError as e:
        raise MappValidationError(f'Invalid JSON: {e}')
    except TypeError as e:
        raise MappValidationError(f'Error creating op output instance: {e}')

op_output_to_json = to_json
op_params_to_json = to_json

def redact_secure_fields(spec:dict, obj:object) -> object:
    """
    Redacts secure fields from a model or op instance.

    Args:
        spec (dict): The specification dictionary for the model or op.
        obj (object): The model or op instance.

    Returns:
        dict: A dictionary representation of the object with secure fields redacted.
    """

    if isinstance(obj, Acknowledgment):
        return obj  # nothing to redact

    replacements = {}

    for field in spec.values():

        field_name = field['name']['snake_case']
        if field['secure']:
            replacements[field_name] = 'REDACTED'

    return obj._replace(**replacements)