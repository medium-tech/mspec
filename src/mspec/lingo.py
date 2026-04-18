import operator

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from random import randint
from typing import Any, Optional
from itertools import dropwhile, takewhile, islice, accumulate
from functools import reduce

from mapp.auth import create_user, login_user, is_logged_in, current_user, logout_user, delete_user, drop_sessions
from mapp.file_system import get_file_content, ingest_start, list_files, get_part_content, list_parts, process_file
from mapp.errors import NotFoundError
from mapp.media import create_image, get_image, get_master_image, get_media_file_content, ingest_master_image, list_images, list_master_images
from mapp.module.model.db import db_model_read, db_model_unique_counts, db_model_query
from mapp.types import get_python_type_for_field, new_model_class

datetime_format_str = '%Y-%m-%dT%H:%M:%S'

@dataclass
class LingoApp:
    spec: dict[str, dict]
    params: dict[str, Any]
    state: dict[str, Any]
    buffer: list[dict]


# # # #
#
# argument mappers | mapping python and lingo function signatures
#
# # # #

def _struct_key_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    object = lingo_execute(app, expression['args']['object'], ctx)
    key = lingo_execute(app, expression['args']['key'], ctx)
    struct_value = object['value'] if isinstance(object, dict) and 'value' in object else object
    key_value = key['value'] if isinstance(key, dict) and 'value' in key else key
    return (struct_value, key_value), {}

def _map_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    
    def map_func(item):
        new_ctx = ctx.copy() if ctx is not None else {}
        new_ctx['self'] = {'item': item}
        result = lingo_execute(app, expression['args']['function'], new_ctx)
        # If result is a dict with 'value' key, extract the value
        # Otherwise return the result as-is (e.g., for link/text dicts)
        if isinstance(result, dict) and 'value' in result:
            return result['value']
        else:
            # Need to recursively evaluate expressions in the dict
            if isinstance(result, dict):
                evaluated_result = {}
                for key, value in result.items():
                    # Recursively evaluate the value, which might contain nested expressions
                    eval_value = lingo_execute(app, value, new_ctx)
                    # Extract value if it's wrapped
                    if isinstance(eval_value, dict) and 'value' in eval_value:
                        evaluated_result[key] = eval_value['value']
                    else:
                        evaluated_result[key] = eval_value
                return evaluated_result
            return result
    
    iterable = lingo_execute(app, expression['args']['iterable'], ctx)
    return (map_func, iterable['value'] if isinstance(iterable, dict) else iterable), {}

def _accumulate_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    
    def accumulate_func(a, b):
        new_ctx = ctx.copy() if ctx is not None else {}
        new_ctx['self'] = {'item': a, 'next_item': b}
        result = lingo_execute(app, expression['args']['function'], new_ctx)
        return result['value']
    
    iterable = lingo_execute(app, expression['args']['iterable'], ctx)
    items = iterable['value'] if isinstance(iterable, dict) else iterable

    initial = expression['args'].get('initial', None)
    return (items, accumulate_func), {'initial': initial}

def _reduce_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    
    def reduce_func(a, b):
        new_ctx = ctx.copy() if ctx is not None else {}
        new_ctx['self'] = {'item': a, 'next_item': b}
        result = lingo_execute(app, expression['args']['function'], new_ctx)
        return result['value']
    
    iterable = lingo_execute(app, expression['args']['iterable'], ctx)
    items = iterable['value'] if isinstance(iterable, dict) else iterable

    initial = expression['args'].get('initial', None)
    if initial is not None:
        return (reduce_func, items, initial), {}
    else:
        return (reduce_func, items), {}
    
#
# auth
#

def _create_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        name_expr = expression['args']['name']
        email_expr = expression['args']['email']
        password_expr = expression['args']['password']
        password_confirm_expr = expression['args']['password_confirm']
    except KeyError as e:
        raise ValueError(f'create_user - missing arg: {e}')

    name = unwrap_primitive(lingo_execute(app, name_expr, ctx))
    email = unwrap_primitive(lingo_execute(app, email_expr, ctx))
    password = unwrap_primitive(lingo_execute(app, password_expr, ctx))
    password_confirm = unwrap_primitive(lingo_execute(app, password_confirm_expr, ctx))

    return (ctx, name, email, password, password_confirm), {}

def _login_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        email_expr = expression['args']['email']
        password_expr = expression['args']['password']
    except KeyError as e:
        raise ValueError(f'login_user - missing arg: {e}')

    email = unwrap_primitive(lingo_execute(app, email_expr, ctx))
    password = unwrap_primitive(lingo_execute(app, password_expr, ctx))

    return (ctx, email, password), {}

def _is_logged_in_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    confirm_expr = expression['args'].get('confirm', False)
    confirm = unwrap_primitive(lingo_execute(app, confirm_expr, ctx))
    return (ctx,), {'confirm': confirm}

def _current_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    # current_user takes no params, only ctx
    return (ctx,), {}

def _logout_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        mode_expr = expression['args']['mode']
    except KeyError as e:
        raise ValueError(f'logout_user - missing arg: {e}')

    mode = unwrap_primitive(lingo_execute(app, mode_expr, ctx))

    return (ctx, mode), {}

def _delete_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    # delete_user takes no params, only ctx
    return (ctx,), {}

def _drop_sessions_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        root_password_expr = expression['args']['root_password']
    except KeyError as e:
        raise ValueError(f'drop_sessions - missing arg: {e}')

    root_password = unwrap_primitive(lingo_execute(app, root_password_expr, ctx))

    return (ctx, root_password), {}

#
# file system
#

def _ingest_start_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        name_expr = expression['args']['name']
        size_expr = expression['args']['size']
        parts_expr = expression['args']['parts']
        content_type_expr = expression['args'].get('content_type', '')
        finish_expr = expression['args'].get('finish', False)
    except KeyError as e:
        raise ValueError(f'ingest_start - missing arg: {e}')

    name = unwrap_primitive(lingo_execute(app, name_expr, ctx))
    size = unwrap_primitive(lingo_execute(app, size_expr, ctx))
    parts = unwrap_primitive(lingo_execute(app, parts_expr, ctx))
    content_type = unwrap_primitive(lingo_execute(app, content_type_expr, ctx))
    finish = unwrap_primitive(lingo_execute(app, finish_expr, ctx))

    return (ctx, name, size, parts, content_type, finish), {}

def _file_system_list_files_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        offset_expr = expression['args']['offset']
        size_expr = expression['args']['size']
        user_id_expr = expression['args']['user_id']
        file_id_expr = expression['args']['file_id']
        status_expr = expression['args']['status']
    except KeyError as e:
        raise ValueError(f'list_files - missing arg: {e}')

    offset = unwrap_primitive(lingo_execute(app, offset_expr, ctx))
    size = unwrap_primitive(lingo_execute(app, size_expr, ctx))
    user_id = unwrap_primitive(lingo_execute(app, user_id_expr, ctx))
    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))
    status = unwrap_primitive(lingo_execute(app, status_expr, ctx))

    return (ctx, offset, size, user_id, file_id, status), {}

def _file_system_get_part_content_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        file_id_expr = expression['args']['file_id']
        part_number_expr = expression['args']['part_number']
    except KeyError as e:
        raise ValueError(f'get_part_content - missing arg: {e}')

    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))
    part_number = unwrap_primitive(lingo_execute(app, part_number_expr, ctx))

    return (ctx, file_id, part_number), {}

def _file_system_get_file_content_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        file_id_expr = expression['args']['file_id']
    except KeyError as e:
        raise ValueError(f'get_file_content - missing arg: {e}')

    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))

    return (ctx, file_id), {}

def _file_system_list_parts_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        file_id_expr = expression['args']['file_id']
        offset_expr = expression['args']['offset']
        size_expr = expression['args']['size']
        user_id_expr = expression['args']['user_id']
    except KeyError as e:
        raise ValueError(f'list_parts - missing arg: {e}')

    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))
    offset = unwrap_primitive(lingo_execute(app, offset_expr, ctx))
    size = unwrap_primitive(lingo_execute(app, size_expr, ctx))
    user_id = unwrap_primitive(lingo_execute(app, user_id_expr, ctx))

    return (ctx, file_id, offset, size, user_id), {}

def _file_system_process_file_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        file_id_expr = expression['args']['file_id']
    except KeyError as e:
        raise ValueError(f'process_file - missing arg: {e}')

    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))

    return (ctx, file_id), {}

#
# media
#

def _media_create_image_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        name_expr = expression['args']['name']
        content_type_expr = expression['args']['content_type']
    except KeyError as e:
        raise ValueError(f'create_image - missing arg: {e}')

    name = unwrap_primitive(lingo_execute(app, name_expr, ctx))
    content_type = unwrap_primitive(lingo_execute(app, content_type_expr, ctx))

    return (ctx, name, content_type), {}

def _media_get_image_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        image_id_expr = expression['args']['image_id']
    except KeyError as e:
        raise ValueError(f'get_image - missing arg: {e}')

    image_id = unwrap_primitive(lingo_execute(app, image_id_expr, ctx))

    return (ctx, image_id), {}

def _media_get_media_file_content_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    image_id_expr = expression['args'].get('image_id')
    master_image_id_expr = expression['args'].get('master_image_id')

    image_id = unwrap_primitive(lingo_execute(app, image_id_expr, ctx)) if image_id_expr is not None else '-1'
    master_image_id = unwrap_primitive(lingo_execute(app, master_image_id_expr, ctx)) if master_image_id_expr is not None else '-1'

    return (ctx, image_id, master_image_id), {}

def _media_list_images_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        offset_expr = expression['args']['offset']
        size_expr = expression['args']['size']
        image_id_expr = expression['args']['image_id']
        file_id_expr = expression['args']['file_id']
        user_id_expr = expression['args']['user_id']
    except KeyError as e:
        raise ValueError(f'list_images - missing arg: {e}')

    offset = unwrap_primitive(lingo_execute(app, offset_expr, ctx))
    size = unwrap_primitive(lingo_execute(app, size_expr, ctx))
    image_id = unwrap_primitive(lingo_execute(app, image_id_expr, ctx))
    file_id = unwrap_primitive(lingo_execute(app, file_id_expr, ctx))
    user_id = unwrap_primitive(lingo_execute(app, user_id_expr, ctx))

    return (ctx, offset, size, image_id, file_id, user_id), {}

def _media_ingest_master_image_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        name_expr = expression['args']['name']
        content_type_expr = expression['args']['content_type']
        thumbnail_max_size_expr = expression['args']['thumbnail_max_size']
    except KeyError as e:
        raise ValueError(f'ingest_master_image - missing arg: {e}')

    name = unwrap_primitive(lingo_execute(app, name_expr, ctx))
    content_type = unwrap_primitive(lingo_execute(app, content_type_expr, ctx))
    thumbnail_max_size = unwrap_primitive(lingo_execute(app, thumbnail_max_size_expr, ctx))

    return (ctx, name, content_type, thumbnail_max_size), {}

def _media_get_master_image_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        master_image_id_expr = expression['args']['master_image_id']
    except KeyError as e:
        raise ValueError(f'get_master_image - missing arg: {e}')

    master_image_id = unwrap_primitive(lingo_execute(app, master_image_id_expr, ctx))

    return (ctx, master_image_id), {}

def _media_list_master_images_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        offset_expr = expression['args']['offset']
        size_expr = expression['args']['size']
        master_image_id_expr = expression['args']['master_image_id']
        user_id_expr = expression['args']['user_id']
    except KeyError as e:
        raise ValueError(f'list_master_images - missing arg: {e}')

    offset = unwrap_primitive(lingo_execute(app, offset_expr, ctx))
    size = unwrap_primitive(lingo_execute(app, size_expr, ctx))
    master_image_id = unwrap_primitive(lingo_execute(app, master_image_id_expr, ctx))
    user_id = unwrap_primitive(lingo_execute(app, user_id_expr, ctx))

    return (ctx, offset, size, master_image_id, user_id), {}

#
# db
#

def _get_model_class_from_type(app:LingoApp, model_type:str) -> type:
    parts = model_type.split('.')
    if len(parts) != 2:
        raise ValueError(f'db - invalid model_type format: {model_type} (expected module.model)')
    module_key, model_key = parts
    try:
        modules = app.spec['modules']
    except KeyError:
        raise ValueError('db - app.spec does not contain modules; ensure op spec is loaded with module context')
    try:
        module_spec = modules[module_key]
    except KeyError:
        raise ValueError(f'db - module not found: {module_key}')
    try:
        model_spec = module_spec['models'][model_key]
    except KeyError:
        raise ValueError(f'db - model not found: {model_key} in module {module_key}')
    return new_model_class(model_spec, module_spec)

def _db_read_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        model_id_expr = expression['args']['model_id']
    except KeyError as e:
        raise ValueError(f'db.read - missing arg: {e}')

    model_type = unwrap_primitive(lingo_execute(app, model_type_expr, ctx))
    model_id = unwrap_primitive(lingo_execute(app, model_id_expr, ctx))
    model_class = _get_model_class_from_type(app, model_type)

    return (ctx, model_class, str(model_id)), {}

def _db_unique_counts_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        group_by_expr = expression['args']['group_by']
    except KeyError as e:
        raise ValueError(f'db.unique_counts - missing arg: {e}')

    model_type = unwrap_primitive(lingo_execute(app, model_type_expr, ctx))
    group_by = unwrap_primitive(lingo_execute(app, group_by_expr, ctx))
    model_class = _get_model_class_from_type(app, model_type)

    filters_expr = expression['args'].get('filters')
    filters = None
    if filters_expr is not None:
        filters_result = lingo_execute(app, filters_expr, ctx)
        if isinstance(filters_result, dict) and 'value' in filters_result:
            raw = filters_result['value']
        else:
            raw = filters_result
        if not isinstance(raw, dict):
            raise ValueError('db.unique_counts - filters arg must be a struct')
        filters = {k: unwrap_primitive(v) for k, v in raw.items()}

    return (ctx, model_class, group_by), {'filters': filters}

def _db_query_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        where_expr = expression['args']['where']
    except KeyError as e:
        raise ValueError(f'db.query - missing arg: {e}')

    model_type = unwrap_primitive(lingo_execute(app, model_type_expr, ctx))
    model_class = _get_model_class_from_type(app, model_type)
    where = unwrap_primitive(lingo_execute(app, where_expr, ctx))

    offset = unwrap_primitive(lingo_execute(app, expression['args']['offset'], ctx)) if 'offset' in expression['args'] else 0
    size = unwrap_primitive(lingo_execute(app, expression['args']['size'], ctx)) if 'size' in expression['args'] else 25


    """
    a fields expression is a struct where each key contains an operator and then a value
    the operator must be a support query operator and the value may be executed as a lingo expression or primitive

    currently support operators:
        eq = equal
        ne = not equal

    example:

        type: struct
        value:
            forum_id:
                eq:
                    params: {forum_id: {}}
            reply_to:
                ne: '-1'
    """

    try:
        condition_items = where.items()
    except (KeyError, AttributeError, TypeError):
        raise ValueError('db.query - where expression must be a struct with value key containing conditions')
    
    conditions = {}

    for field_name, condition in condition_items:
        if not isinstance(condition, dict) or len(condition) != 1:
            raise ValueError(f'db.query - each field condition must be a struct with a single operator: {field_name}')
        
        operator, operand_expr = next(iter(condition.items()))
        if operator not in ('eq', 'ne'):
            raise ValueError(f'db.query - unsupported operator: {operator} in field condition for field {field_name}')
        
        operand_value = lingo_execute(app, operand_expr, ctx)
        conditions[field_name] = {operator: unwrap_primitive(operand_value)}

    return (ctx, model_class, conditions, offset, size), {}

def db_read(ctx, model_class, model_id:str) -> dict:
    try:
        model = db_model_read(ctx, model_class, model_id)
        return {'type': 'struct', 'value': model._asdict()}
    except NotFoundError as e:
        raise
        return {
            'error': {
                'code': 'MODEL_NOT_FOUND',
                'message': str(e)
            }
        }

def db_unique_counts(ctx, model_class, group_by:str, filters=None) -> list:
    rows = db_model_unique_counts(ctx, model_class, group_by, filters)
    return [{'type': 'struct', 'value': row} for row in rows]

def db_query(ctx, model_class, where:dict, offset:int=0, size:int=25) -> list:
    return db_model_query(ctx, model_class, where, offset, size)

def str_convert(object:Any) -> str:
    if object is True:
        return 'true'
    elif object is False:
        return 'false'
    else:
        return str(object)

def str_join(separator:str, items:list) -> str:
    return separator.join(str(item) for item in items)

def str_concat(items:list) -> str:
    return ''.join(str(item) for item in items)

def struct_key(object:dict, key_name:str) -> Any:
    try:
        return object[key_name]
    except KeyError:
        raise ValueError(f'struct_key - key not found in struct: {key_name}')

def lingo_int(number:Any=None, string:str=None, base:int=10) -> int:
    if number is not None:
        return int(number)

    elif string is not None:
        return int(string, base)
        
    else:
        raise ValueError('lingo int - must provide either number or string argument')

def unwrap_primitive(value:Any) -> Any:
    if isinstance(value, dict) and 'type' in value:
        try:
            return value['value']
        except KeyError:
            raise ValueError('Invalid value element - missing value key')
    else:
        return value

def lingo_type_from_py_obj(object:Any) -> str:
    if isinstance(object, bool):
        return 'bool'
    elif isinstance(object, int):
        return 'int'
    elif isinstance(object, float):
        return 'float'
    elif isinstance(object, str):
        return 'str'
    elif isinstance(object, list):
        return 'list'
    elif isinstance(object, dict):
        return 'struct'
    else:
        return 'any'


lingo_function_lookup = {

    # comparison #

    'eq': {'func': operator.eq, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},
    'ne': {'func': operator.ne, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},
    'lt': {'func': operator.lt, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},
    'le': {'func': operator.le, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},
    'gt': {'func': operator.gt, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},
    'ge': {'func': operator.ge, 'args': {'a': {'type': ('int', 'float', 'str')}, 'b': {'type': ('int', 'float', 'str')}}},

    # bool #

    'bool': {'func': bool, 'args': {'object': {'type': 'any'}}},
    'not': {'func': operator.not_, 'args': {'object': {'type': 'any'}}},
    'and': {'func': operator.and_, 'args': {'a': {'type': 'any'}, 'b': {'type': 'any'}}},
    'or': {'func': operator.or_, 'args': {'a': {'type': 'any'}, 'b': {'type': 'any'}}},

    # int #

    'int': {'func': lingo_int, 'args': {'number': {'type': 'any', 'default': None}, 'string': {'type': 'str', 'default': None}, 'base': {'type': 'int', 'default': 10}}},
    'neg': {'func': operator.neg, 'args': {'object': {'type': 'any'}}},

    # float #

    'float': {'func': float, 'args': {'number': {'type': 'any'}}},
    'round': {'func': round, 'args': {'number': {'type': 'float'}, 'ndigits': {'type': 'int', 'default': None}}},

    # str #

    'str': {'func': str_convert, 'args': {'object': {'type': 'any'}}},
    'join': {'func': str_join, 'args': {'separator': {'type': 'str'}, 'items': {'type': 'list'}}},
    'concat': {'func': str_concat, 'args': {'items': {'type': 'list'}}},

    # struct #

    'key': {'func': struct_key, 'create_args': _struct_key_args},

    # math #

    'add': {'func': operator.add, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'sub': {'func': operator.sub, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'mul': {'func': operator.mul, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'div': {'func': operator.truediv, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'floordiv': {'func': operator.floordiv, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'mod': {'func': operator.mod, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    # 'divmod': {'func': divmod, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}}, - need to accept multi-dim lists
    'pow': {'func': operator.pow, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'min': {'func': min, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'max': {'func': max, 'args': {'a': {'type': ('int', 'float')}, 'b': {'type': ('int', 'float')}}},
    'abs': {'func': abs, 'args': {'number': {'type': ('int', 'float')}}},

    # sequence #

    'len': {'func': len, 'args': {'object': {'type': ('str', 'list')}}},
    'range': {'func': range, 'args': {'start': {'type': 'int', 'default': 0}, 'stop': {'type': 'int'}, 'step': {'type': 'int', 'default': 1}}},
    'slice': {'func': islice, 'args': {'iterator': {'type': 'list'}, 'start': {'type': 'int', 'default': None}, 'stop': {'type': 'int'}, 'step': {'type': 'int', 'default': None}}},
    'any': {'func': any, 'args': {'iterable': {'type': 'list'}}},
    'all': {'func': all, 'args': {'iterable': {'type': 'list'}}},
    'sum': {'func': lambda i, s: sum(i, s), 'args': {'iterable': {'type': 'list'}, 'start': {'type': ('int', 'float'), 'default': 0}}},
    'sorted': {'func': sorted, 'args': {'iterable': {'type': 'list'}}},

    # sequence ops #

    'map': {'func': map, 'create_args': _map_function_args},
    'filter': {'func': filter, 'create_args': _map_function_args},
    'dropwhile': {'func': dropwhile, 'create_args': _map_function_args},
    'takewhile': {'func': takewhile, 'create_args': _map_function_args},
    'reversed': {'func': reversed, 'args': {'sequence': {'type': 'list'}}},
    'accumulate': {'func': accumulate, 'create_args': _accumulate_function_args},
    'reduce': {'func': reduce, 'create_args': _reduce_function_args},

    # date and time #

    'current': {
        'weekday': {'func': lambda: datetime.now().weekday(), 'args': {}, 'sig': 'kwargs'}
    },
    'datetime': {
        'now': {'func': datetime.now, 'args': {}, 'sig': 'kwargs'}
    },

    # random #

    'random': {
        'randint': {'func': randint, 'args': {'a': {'type': 'int'}, 'b': {'type': 'int'}}, 'sig': 'kwargs'}
    },

    # auth #

    'auth': {
        'create_user': {'func': create_user, 'create_args': _create_user_function_args},
        'login_user': {'func': login_user, 'create_args': _login_user_function_args},
        'is_logged_in': {'func': is_logged_in, 'create_args': _is_logged_in_function_args},
        'current_user': {'func': current_user, 'create_args': _current_user_function_args},
        'logout_user': {'func': logout_user, 'create_args': _logout_user_function_args},
        'delete_user': {'func': delete_user, 'create_args': _delete_user_function_args},
        'drop_sessions': {'func': drop_sessions, 'create_args': _drop_sessions_function_args}
    },

    # file system #

    'file_system': {
        'ingest_start': {'func': ingest_start, 'create_args': _ingest_start_function_args},
        'list_files': {'func': list_files, 'create_args': _file_system_list_files_function_args},
        'list_parts': {'func': list_parts, 'create_args': _file_system_list_parts_function_args},
        'get_part_content': {'func': get_part_content, 'create_args': _file_system_get_part_content_function_args},
        'get_file_content': {'func': get_file_content, 'create_args': _file_system_get_file_content_function_args},
        'process_file': {'func': process_file, 'create_args': _file_system_process_file_function_args}
    },

    # media #

    'media': {
        'create_image': {'func': create_image, 'create_args': _media_create_image_function_args},
        'get_image': {'func': get_image, 'create_args': _media_get_image_function_args},
        'get_master_image': {'func': get_master_image, 'create_args': _media_get_master_image_function_args},
        'get_media_file_content': {'func': get_media_file_content, 'create_args': _media_get_media_file_content_function_args},
        'ingest_master_image': {'func': ingest_master_image, 'create_args': _media_ingest_master_image_function_args},
        'list_images': {'func': list_images, 'create_args': _media_list_images_function_args},
        'list_master_images': {'func': list_master_images, 'create_args': _media_list_master_images_function_args}
    },

    # db #

    'db': {
        'read': {'func': db_read, 'create_args': _db_read_function_args},
        'unique_counts': {'func': db_unique_counts, 'create_args': _db_unique_counts_function_args},
        'query': {'func': db_query, 'create_args': _db_query_function_args},
    }
}

# # # #
#
# lingo interpreter
#
# # # #

def lingo_app(spec: dict, **params) -> LingoApp:
    instance = LingoApp(spec=deepcopy(spec), params=params, state={}, buffer=[])

    for arg_name in params.keys():
        if arg_name not in instance.spec['params']:
            raise ValueError(f'argument {arg_name} not defined in spec')

    return lingo_update_state(instance)

def lingo_update_state(app:LingoApp, ctx: Optional[dict]=None) -> LingoApp:
    for key, value in app.spec['state'].items():
        try:
            calc = value['calc']
        except KeyError:
            # this is a non-calculated value, set state to default is not already set
            if key not in app.state:
                try:
                    if value['type'] != lingo_type_from_py_obj(value['default']):
                        raise ValueError(f'state - {key} - default value type mismatch')
                    app.state[key] = value['default']
                except KeyError:
                    raise ValueError(f'state - {key} - missing default value')
        else:
            new_value = lingo_execute(app, calc, ctx)
            if not isinstance(new_value, dict) or 'value' not in new_value or 'type' not in new_value:
                raise ValueError(f'state - {key} - expression did not return a valid value dict')
            if value['type'] != new_value['type']:
                raise ValueError(f'state - {key} - expression returned type: ' + new_value['type'] +
                                 f', expected type: {value["type"]}')
            app.state[key] = new_value['value']

    return app

def lingo_execute(app:LingoApp, expression:Any, ctx:Optional[dict]=None) -> Any:
    """
    Run the expression and return the result.
    :param
        expression: dict - The expression to run."
    :return: Any - The result of the expression."
    """

    # calculate expression #

    if isinstance(expression, dict):
        if 'set' in expression:
            result = render_set(app, expression, ctx)
        elif 'state' in expression:
            result = render_state(app, expression, ctx)
        elif 'params' in expression:
            result = render_params(app, expression, ctx)
        elif 'op' in expression:
            result = render_op(app, expression, ctx)
        elif 'call' in expression:
            result = render_call(app, expression, ctx)
        elif 'block' in expression:
            result = render_block(app, expression, ctx)
        elif 'lingo' in expression:
            result = render_lingo(app, expression, ctx)
        elif 'branch' in expression:
            result = render_branch(app, expression, ctx)
        elif 'switch' in expression:
            result = render_switch(app, expression, ctx)
        elif 'heading' in expression:
            # heading is a special case for rendering headings
            result = render_heading(app, expression, ctx)
        elif 'args' in expression:
            result = render_args(app, expression, ctx)
        elif 'self' in expression:
            result = render_self(app, expression, ctx)
        elif 'value' in expression:
            result = render_value(app, expression, ctx)
        else:
            result = expression
    else:
        result = expression

    # format return value #

    if isinstance(result, (dict, list)):
        return result
    
    else:
        if not isinstance(result, (bool, int, float, str, datetime)):
            raise ValueError(f'Unsupported return type: {result.__class__.__name__}')
        
        return {'value': result, 'type': result.__class__.__name__}

#
# high level render
#

def render_output(app:LingoApp, ctx:Optional[dict]=None) -> list[dict]:
    app.buffer = []
    for n, element in enumerate(app.spec['output']):
        try:
            rendered = lingo_execute(app, element, ctx)
            if isinstance(rendered, dict):
                app.buffer.append(rendered)
            elif isinstance(rendered, list):
                for item in rendered:
                    if isinstance(item, dict):
                        app.buffer.append(item)
                    else:
                        raise ValueError(f'Rendered output item is not a dict: {item.__class__.__name__} - output {n}')
            else:
                raise ValueError(f'Rendered output is not a dict or list: {rendered.__class__.__name__} - output {n}')
        except ValueError as e:
            raise ValueError(f'Render error - output {n} - {e}')
        except Exception as e:
            raise ValueError(f'Render error - output {n} - {e.__class__.__name__}{e}')
    return app.buffer

def render_block(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    elements = []
    for n, child_element in enumerate(element['block']):
        try:
            elements.append(lingo_execute(app, child_element, ctx))
        except ValueError as e:
            raise ValueError(f'block error, element {n}: {e}')
    return elements

#
# control flow
#

def render_branch(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    branches = element['branch']
    num_branches = len(branches)
    last_index = num_branches - 1
    if num_branches < 2:
        raise ValueError('branch - must have at least 2 cases')
    
    if 'else' not in branches[-1]:
        raise ValueError('branch - last element must be else case')
    
    for n, branch in enumerate(branches):

        # get expression for branch #

        try:
            expr = branch['if']
            if n != 0:
                raise ValueError('branch 0 - must be if case')
        except KeyError:
            try:
                expr = branch['elif']
                if n == 0 or n == last_index:
                    raise ValueError(f'branch {n} - elif must not be first or last case')
            except KeyError:
                try:
                    branch['else']
                    expr = True
                    if n != last_index:
                        raise ValueError(f'branch {n} - else case must be last case')
                except KeyError:
                    raise ValueError(f'branch {n} - missing if/elif/else key')

        try:
            then = branch['then']
        except KeyError:
            try:
                # for else statements, the else keyword functions as the then statement
                then = branch['else']
            except KeyError:
                raise ValueError(f'branch {n} - missing then expression')
        
        # run expresion #

        try:
            condition = lingo_execute(app, expr, ctx)['value']
        except Exception as e:
            raise ValueError(f'branch {n} - error processing condition') from e

        if condition:
            try:
                value = lingo_execute(app, then, ctx)
                return value
            except Exception as e:
                raise ValueError(f'branch {n} - error processing then expression') from e

    raise ValueError(f'unvalid branch expression')

def render_switch(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    try:
        switch = element['switch']
        expression = switch['expression']
        cases = switch['cases']
        default = switch['default']
    except KeyError as e:
        raise ValueError(f'switch - missing key: {e}')
    
    if len(cases) == 0:
        raise ValueError(f'switch - must have at least one case')

    try:
        value = lingo_execute(app, expression, ctx)['value']
    except Exception as e:
        raise ValueError(f'switch - error processing expression') from e

    for case in cases:
        try:
            if value == case['case']:
                return lingo_execute(app, case['then'], ctx)
        except Exception as e:
            raise ValueError(f'switch - error processing case') from e
    
    return lingo_execute(app, default, ctx)

#
# state and input
#

def render_self(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    try:
        return ctx['self'][expression['self']]
    except (KeyError, TypeError):
        raise ValueError('self - missing self context')

def render_params(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    # parse expression #

    field_names = list(expression['params'].keys())
    if len(field_names) != 1:
        raise ValueError('params - must have exactly one param field')
    field_name = field_names[0]

    # get definition #

    try:
        param_def = app.spec['params'][field_name]
    except KeyError:
        raise ValueError(f'params - undefined field: {field_name}')
    
    # validate value #

    try:
        if isinstance(app.params, dict):
            value = app.params[field_name]
        else:
            value = getattr(app.params, field_name)
    except (KeyError, AttributeError):
        try:
            value = param_def['default']
        except KeyError:
            raise ValueError(f'params - missing value for field: {field_name}')
    actual_py_type = type(value)
    expected_py_type = get_python_type_for_field(param_def['type'])
    if actual_py_type != expected_py_type:
        raise ValueError(f'params - expected {expected_py_type} for {field_name} got: {actual_py_type}')
    
    # return value #
    
    return value

def render_set(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    try:
        target = expression['set']['state']
        value_expr = expression['to']
    except KeyError as e:
        raise ValueError(f'set - missing key: {e}')
    
    # get field info #

    try:
        field_names = list(target.keys())
        if len(field_names) != 1:
            raise ValueError('set - must have exactly one state field')
        field_name = field_names[0]
    except IndexError:
        raise ValueError('set - missing state field')
    
    field_type = app.spec['state'][field_name]['type']
    
    # get value #

    try:
        value = lingo_execute(app, value_expr, ctx)['value']
    except Exception as e:
        raise ValueError('set - error processing to expression') from e
    
    if value.__class__.__name__ != field_type:
        raise ValueError(f'set - value type mismatch: {field_type} != {value.__class__.__name__}')
    
    app.state[field_name] = value
    return app.state[field_name]

def render_state(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    # parse expression #

    field_names = list(expression['state'].keys())
    if len(field_names) != 1:
        raise ValueError('state - must have exactly one state field')
    field_name = field_names[0]

    # get value #
    
    try:
        return app.state[field_name]
    except KeyError:
        raise ValueError(f'state - field not found: {field_name}')

#
# expressions
#

def render_lingo(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    result = lingo_execute(app, element['lingo'], ctx)
    _type = type(result)

    convert = lambda x: x.strftime(datetime_format_str) if isinstance(x, datetime) else str(x)

    if _type == dict:
        if 'value' in result:
            if result['type'] in ['str', 'int', 'float', 'bool', 'datetime']:
                return {'text': convert(result['value'])}
            elif result['type'] == 'list':
                return {'text': ', '.join(convert(item) for item in result['value'])}
            else:
                raise ValueError(f'lingo - unexpected result value type: {result["type"]}')
        else:
            return result
    elif _type == list:
        return {'text': ', '.join(convert(item) for item in result)}
    else:
        raise ValueError(f'lingo - invalid result type: {_type}')
    
def render_heading(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> dict:
    
    try:
        if not 1 <= element['level'] <= 6:
            raise ValueError('heading - level must be between 1 and 6')
    except KeyError:
        raise ValueError('heading - missing level key')
    
    if isinstance(element['heading'], str):
        heading = element['heading']
    else:
        try:
            heading = lingo_execute(app, element['heading'], ctx)
        except Exception as e:
            raise ValueError('heading - error processing heading expression') from e
    
    if isinstance(heading, dict) and 'text' in heading:
        heading_text = heading['text']
    elif isinstance(heading, dict) and 'value' in heading:
        heading_text = str(heading['value'])
    elif isinstance(heading, str):
        heading_text = heading
    elif isinstance(heading, (bool, int, float)):
        heading_text = str(heading)
    else:
        raise ValueError(f'heading - invalid heading type: {heading.__class__.__name__} - expected str or dict with text key')
    
    try:
        return {'heading': heading_text, 'level': element['level']}
    except KeyError:
        raise ValueError('heading - missing level key')

def render_op(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    # input #
    keys = list(expression['op'].keys())
    if len(keys) != 1:
        raise ValueError('op - must have exactly one op field')
    op_name = keys[0]
    op_args = expression['op'][op_name]

    # get op #
    try:
        op_def = app.spec['ops'][op_name]
    except KeyError:
        raise ValueError(f'op - undefined op: {op_name}')
    
    try:
        func = op_def['func']
    except KeyError:
        raise ValueError(f'op - missing func for op: {op_name}')
    
    # execute #
    return lingo_execute(app, func, op_args)

def render_call(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:

    # init #

    try:
        _args = expression['args']
    except KeyError:
        _args = {}

    name_split = expression['call'].split('.')
    name_depth = len(name_split)
    if not 1 <= name_depth <= 2:
        raise ValueError('call - invalid function name')
    
    # get func and args def #

    try:
        if name_depth == 1:
            definition = lingo_function_lookup[name_split[0]]
            
        else:
            definition = lingo_function_lookup[name_split[0]][name_split[1]]

    except KeyError as func_name:
        raise ValueError(f'call - undefined func: {func_name}')
    
    function = definition['func']
    args_def = definition.get('args', {})
        
    # supplied args #

    rendered_args = {}
    if 'create_args' not in definition:
        for arg_name, arg_expression in _args.items():
            try:
                arg_type = args_def[arg_name]['type']
            except KeyError:
                raise ValueError(f'call - unknown arg: {arg_name}')
            
            value = lingo_execute(app, arg_expression, ctx)

            # If value is a list, we need to evaluate any dict expressions in it
            if isinstance(value, list):
                evaluated_list = []
                for item in value:
                    if isinstance(item, dict) and not ('value' in item and 'type' in item):
                        # It's an unevaluated expression - evaluate it with the current context
                        eval_item = lingo_execute(app, item, ctx)
                        if isinstance(eval_item, dict) and 'value' in eval_item:
                            evaluated_list.append(eval_item['value'])
                        else:
                            evaluated_list.append(eval_item)
                    else:
                        # It's a literal value
                        evaluated_list.append(item)
                rendered_args[arg_name] = evaluated_list
            else:
                try:
                    rendered_args[arg_name] = value['value']
                except TypeError:
                    rendered_args[arg_name] = value

    # order args and call #

    if definition.get('sig', '') == 'kwargs':
        return_value = function(**rendered_args)
    
    # create args from callable
    elif 'create_args' in definition:
        # custom arg handling
        args, kwargs = definition['create_args'](app, expression, ctx)
        try:
            return_value = function(*args, **kwargs)
        except Exception as e:
            raise e

    else: 
        # positional args
        args_list = []
        for arg_name in args_def.keys():
            if arg_name in rendered_args:
                args_list.append(rendered_args[arg_name])
            elif 'default' in args_def[arg_name]:
                args_list.append(args_def[arg_name]['default'])
            else:
                raise ValueError(f'call - missing required arg: {arg_name}')

        return_value = function(*args_list)
    
    # format return value #

    if hasattr(return_value, '__iter__') and not isinstance(return_value, (str, dict)):
        element_types = []
        elements = []
        for item in return_value:
            if not isinstance(item, (bool, int, float, str, dict, datetime)):
                raise ValueError(f'List contains unsupported type: {item.__class__.__name__}')
            element_types.append(item.__class__.__name__)
            elements.append(item)
        if len(set(element_types)) > 1:
            raise ValueError(f'List contains mixed types: {element_types}')
        
        try:
            element_type = element_types[0]
        except IndexError:
            element_type = 'unknown'
        
        return {'value': elements, 'type': 'list', 'element_type': element_type}
    
    else:
        return return_value

def render_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    arg_name = expression['args']
    try:
        return ctx[arg_name]
    except KeyError:
        raise ValueError(f'args - undefined arg: {arg_name}')

def render_value(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    """
    if primitive value: execute possible expression and return value

    if list: iterate over items and execute expressions, return list of results

    if struct: execute expressions for each field and return dict of results
    
    """

    try:
        _type = expression['type']
    except KeyError:
        raise ValueError('value - missing type key')
    
    match _type:
        case 'bool' | 'int' | 'float' | 'str' | 'datetime':
            if isinstance(expression['value'], dict):
                try:
                    return lingo_execute(app, expression['value'], ctx)
                except Exception as e:
                    raise ValueError('value - error processing expression') from e
            else:
                return expression
        
        case 'list':
            if not isinstance(expression['value'], list):
                raise ValueError('value - expected list value')
            
            result_list = []
            for n, item in enumerate(expression['value']):
                if isinstance(item, dict):
                    try:
                        result_list.append(lingo_execute(app, item, ctx))
                    except Exception as e:
                        raise ValueError(f'value - error processing list item {n}') from e
                else:
                    result_list.append(item)
            
            expression['value'] = result_list

            return expression
        
        case 'struct':
            if not isinstance(expression['value'], dict):
                raise ValueError('value - expected struct value')
            
            result_struct = {}
            for field_name, field_value in expression['value'].items():
                if isinstance(field_value, dict):
                    try:
                        result_struct[field_name] = lingo_execute(app, field_value, ctx)
                    except NotFoundError as e:
                        raise e
                    except Exception as e:
                        raise ValueError(f'value - error processing struct field {field_name}') from e
                else:
                    result_struct[field_name] = field_value
            
            expression['value'] = result_struct
            return expression
        
        case _:
            raise ValueError(f'value - unsupported type: {_type}')