import math
import operator
import re

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from random import randint
from typing import Any, Optional
from itertools import dropwhile, takewhile, islice, accumulate
from functools import reduce

from mapp.auth import create_user, login_user, invite_user, is_logged_in, current_user, logout_user, delete_user, drop_sessions
from mapp.com import send_email, start_email_verification, verify_email_address
from mapp.context import MappContext
from mapp.file_system import get_file_content, ingest_start, list_files, get_part_content, list_parts, process_file
from mapp.errors import NotFoundError, MappValidationError, AuthenticationError
from mapp.media import create_image, get_image, get_master_image, get_media_file_content, ingest_master_image, list_images, list_master_images
from mapp.module.model.db import db_model_create, db_model_read, db_model_update, db_model_delete, db_model_unique_counts, db_model_query
from mapp.types import get_python_type_for_field, new_model_class, convert_dict_to_model

datetime_format_str = '%Y-%m-%dT%H:%M:%S'
db_query_batch_size = 1000000
db_upsert_conflict_check_size = 2

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
    default_value = expression['args'].get('default_value', None)
    struct_value = object['value'] if isinstance(object, dict) and 'value' in object else object
    key_value = key['value'] if isinstance(key, dict) and 'value' in key else key
    return (struct_value, key_value, default_value), {}

def _map_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    # ctx.log(f'map_function_args -, ctx: {ctx.self.keys()}')
    def map_func(item):
        if isinstance(ctx, MappContext):
            new_ctx = MappContext(
                server_port=ctx.server_port,
                client=ctx.client,
                db=ctx.db,
                log=ctx.log,
                current_access_token=ctx.current_access_token,
                self=deepcopy(ctx.self)
            )
            new_ctx.self.update({'item': item})
        else:
            new_ctx = ctx.copy() if ctx is not None else {'self': {}}
            new_ctx['self'].update({'item': item})
        
        result = lingo_execute(app, deepcopy(expression['args']['function']), new_ctx)
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
                    eval_value = lingo_execute(app, deepcopy(value), new_ctx)
                    # Extract value if it's wrapped
                    if isinstance(eval_value, dict) and 'value' in eval_value:
                        evaluated_result[key] = eval_value['value']
                    else:
                        evaluated_result[key] = eval_value
                return evaluated_result
            return result
        
    # def debug_wrapper(item):
    #     breakpoint()
    #     result = map_func(item)
    #     breakpoint()
    #     return result
    
    iterable = lingo_execute(app, expression['args']['iterable'], ctx)
    return (map_func, iterable['value'] if isinstance(iterable, dict) else iterable), {}


def _indexed_map_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    '''map function args that include the iteration index in the self context as self.index'''
    def map_func(idx_item_tuple):
        idx, item = idx_item_tuple
        if isinstance(ctx, MappContext):
            new_ctx = MappContext(
                server_port=ctx.server_port,
                client=ctx.client,
                db=ctx.db,
                log=ctx.log,
                current_access_token=ctx.current_access_token,
                self=deepcopy(ctx.self)
            )
            new_ctx.self.update({'item': item, 'index': idx})
        else:
            new_ctx = ctx.copy() if ctx is not None else {'self': {}}
            new_ctx['self'].update({'item': item, 'index': idx})
        
        result = lingo_execute(app, deepcopy(expression['args']['function']), new_ctx)
        if isinstance(result, dict) and 'value' in result:
            return result['value']
        else:
            if isinstance(result, dict):
                evaluated_result = {}
                for key, value in result.items():
                    eval_value = lingo_execute(app, deepcopy(value), new_ctx)
                    if isinstance(eval_value, dict) and 'value' in eval_value:
                        evaluated_result[key] = eval_value['value']
                    else:
                        evaluated_result[key] = eval_value
                return evaluated_result
            return result

    iterable = lingo_execute(app, expression['args']['iterable'], ctx)
    iterable_value = iterable['value'] if isinstance(iterable, dict) else iterable
    return (map_func, enumerate(iterable_value)), {}

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

def _invite_user_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
	try:
		email_expr = expression['args']['email']
	except KeyError as e:
		raise ValueError(f'invite_user - missing arg: {e}')

	email = unwrap_primitive(lingo_execute(app, email_expr, ctx))

	return (ctx, email), {}

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
# com
#

def _send_email_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        email_expr = expression['args']['email']
        subject_expr = expression['args']['subject']
        body_expr = expression['args']['body']
    except KeyError as e:
        raise ValueError(f'send_email - missing arg: {e}')

    email = unwrap_primitive(lingo_execute(app, email_expr, ctx))
    subject = unwrap_primitive(lingo_execute(app, subject_expr, ctx))
    body = unwrap_primitive(lingo_execute(app, body_expr, ctx))

    return (ctx, email, subject, body), {}

def _start_email_verification_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    return (ctx,), {}

def _verify_email_address_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        code_expr = expression['args']['code']
    except KeyError as e:
        raise ValueError(f'verify_email_address - missing arg: {e}')

    code = unwrap_primitive(lingo_execute(app, code_expr, ctx))

    return (ctx, code), {}

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
    return new_model_class(app.spec, model_spec, module_spec)

def _resolve_expression_value(app:LingoApp, expression: Any, ctx:Optional[dict]=None) -> Any:
    if isinstance(expression, dict) and not ('type' in expression and 'value' in expression):
        expression = lingo_execute(app, expression, ctx)
    return unwrap_primitive(expression)

def _resolve_struct_expression(app:LingoApp, expression: Any, ctx:Optional[dict], error_message: str) -> dict:
    result = lingo_execute(app, expression, ctx)
    if isinstance(result, dict) and result.get('type') == 'struct':
        result = result['value']
    if not isinstance(result, dict):
        raise ValueError(error_message)
    return result

def _resolve_list_expression(app:LingoApp, expression: Any, ctx:Optional[dict], error_message: str) -> list:
    result = lingo_execute(app, expression, ctx)
    if isinstance(result, dict) and result.get('type') == 'list':
        result = result['value']
    if not isinstance(result, list):
        raise ValueError(error_message)
    return result

def _db_create_data_dict(app:LingoApp, data_expr: Any, ctx:Optional[dict]) -> dict:
    input_data = _resolve_struct_expression(app, data_expr, ctx, 'db.create - data expression must evaluate to a struct')
    data = {}

    for field_name, field_expression in input_data.items():
        field_value = lingo_execute(app, field_expression, ctx)

        if isinstance(field_value, list):
            items = []
            for item in field_value:
                if isinstance(item, dict) and not ('type' in item and 'value' in item):
                    item = lingo_execute(app, item, ctx)
                items.append(unwrap_primitive(item))
            data[field_name] = items
        else:
            data[field_name] = unwrap_primitive(field_value)

    return data

def _db_parse_where_conditions(app:LingoApp, where_expr: Any, ctx:Optional[dict], error_prefix: str, legacy_fields: bool=False) -> dict:
    where = _resolve_struct_expression(app, where_expr, ctx, f'{error_prefix} - where expression must be a struct')
    conditions = {}

    for field_name, condition in where.items():
        if legacy_fields and _db_is_legacy_fields_condition(condition):
            # Backward compatibility: legacy `fields` accepts {field: value} and maps it to eq.
            operand_value = lingo_execute(app, condition, ctx)
            conditions[field_name] = {'eq': unwrap_primitive(operand_value)}
            continue

        if not isinstance(condition, dict) or len(condition) != 1:
            raise ValueError(f'{error_prefix} - each field condition must be a struct with a single operator: {field_name}')

        operator, operand_expr = next(iter(condition.items()))
        if operator not in ('eq', 'ne'):
            raise ValueError(f'{error_prefix} - unsupported operator: {operator} in field condition for field {field_name}')

        operand_value = lingo_execute(app, operand_expr, ctx)
        conditions[field_name] = {operator: unwrap_primitive(operand_value)}

    return conditions

def _db_is_legacy_fields_condition(condition: Any) -> bool:
    if not isinstance(condition, dict):
        return True
    if len(condition) != 1:
        return True
    return next(iter(condition.keys())) not in ('eq', 'ne')

def _db_parse_include_spec(app:LingoApp, include_expr: Any, ctx:Optional[dict]) -> dict:
    include = _resolve_struct_expression(app, include_expr, ctx, 'db.include - include expression must evaluate to a struct')

    try:
        alias = _resolve_expression_value(app, include['alias'], ctx)
        model_type = _resolve_expression_value(app, include['model_type'], ctx)
        local_field = _resolve_expression_value(app, include['local_field'], ctx)
        foreign_field = _resolve_expression_value(app, include['foreign_field'], ctx)
        fields = _resolve_list_expression(app, include['fields'], ctx, 'db.include - include.fields must evaluate to a list')
    except KeyError as e:
        raise ValueError(f'db.include - missing required include key: {e}')

    cardinality = _resolve_expression_value(app, include.get('cardinality', 'one'), ctx)
    if cardinality not in ('one', 'many'):
        raise ValueError(f'db.include - unsupported cardinality: {cardinality}')

    model_class = _get_model_class_from_type(app, str(model_type))
    field_list = [str(field_name) for field_name in fields]

    return {
        'alias': str(alias),
        'model_class': model_class,
        'local_field': str(local_field),
        'foreign_field': str(foreign_field),
        'fields': field_list,
        'cardinality': str(cardinality),
    }

def _db_parse_unique_counts_specs(app:LingoApp, unique_counts_expr: Any, ctx:Optional[dict]) -> list:
    unique_counts = _resolve_list_expression(app, unique_counts_expr, ctx, 'db.query - unique_counts must evaluate to a list')
    parsed = []

    for index, unique_count in enumerate(unique_counts):
        if isinstance(unique_count, dict) and unique_count.get('type') == 'struct':
            unique_count = unique_count['value']

        if not isinstance(unique_count, dict):
            raise ValueError(f'db.query - unique_counts[{index}] must be a struct')

        try:
            alias = _resolve_expression_value(app, unique_count['alias'], ctx)
            model_type = _resolve_expression_value(app, unique_count['model_type'], ctx)
            source_field = _resolve_expression_value(app, unique_count['source_field'], ctx)
            foreign_field = _resolve_expression_value(app, unique_count['foreign_field'], ctx)
            group_by = _resolve_expression_value(app, unique_count['group_by'], ctx)
        except KeyError as e:
            raise ValueError(f'db.query - unique_counts[{index}] missing key: {e}')

        parsed.append({
            'alias': str(alias),
            'model_class': _get_model_class_from_type(app, str(model_type)),
            'source_field': str(source_field),
            'foreign_field': str(foreign_field),
            'group_by': str(group_by),
        })

    return parsed

def _db_parse_sort_specs(app:LingoApp, sort_expr: Any, ctx:Optional[dict]) -> list:
    sort_specs = _resolve_list_expression(app, sort_expr, ctx, 'db.query - sort must evaluate to a list')
    parsed = []

    for index, sort_spec in enumerate(sort_specs):
        if isinstance(sort_spec, dict) and sort_spec.get('type') == 'struct':
            sort_spec = sort_spec['value']

        if not isinstance(sort_spec, dict):
            raise ValueError(f'db.query - sort[{index}] must be a struct')

        try:
            field = _resolve_expression_value(app, sort_spec['field'], ctx)
            order = _resolve_expression_value(app, sort_spec['order'], ctx)
        except KeyError as e:
            raise ValueError(f'db.query - sort[{index}] missing key: {e}')

        if not isinstance(order, str):
            raise ValueError(f'db.query - sort[{index}] order must be a string')
        order_value = order.lower()
        if order_value not in ('asc', 'desc'):
            raise ValueError(f'db.query - sort[{index}] order must be "asc" or "desc"')

        parsed.append({
            'field': str(field),
            'order': order_value,
        })

    return parsed

def _db_read_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        model_id_expr = expression['args']['model_id']
    except KeyError as e:
        raise ValueError(f'db.read - missing arg: {e}')

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_id = _resolve_expression_value(app, model_id_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    kwargs = {}

    include_expr = expression['args'].get('include')
    if include_expr is not None:
        kwargs['include'] = _db_parse_include_spec(app, include_expr, ctx)

    return (ctx, model_class, str(model_id)), kwargs

def _db_create_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        data_expr = expression['args']['data']
    except KeyError as e:
        raise ValueError(f'db.create - missing arg: {e}')

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    data = _db_create_data_dict(app, data_expr, ctx)

    return (ctx, model_class, data), {}

def _db_patch_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        model_id_expr = expression['args']['model_id']
        data_expr = expression['args']['data']
    except KeyError as e:
        raise ValueError(f'db.patch - missing arg: {e}')

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_id = _resolve_expression_value(app, model_id_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    data = _db_create_data_dict(app, data_expr, ctx)

    return (ctx, model_class, str(model_id), data), {}

def _db_upsert_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        data_expr = expression['args']['data']
        conflict_fields_expr = expression['args']['conflict_fields']
    except KeyError as e:
        raise ValueError(f'db.upsert - missing arg: {e}')

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    data = _db_create_data_dict(app, data_expr, ctx)
    conflict_fields_raw = _resolve_list_expression(app, conflict_fields_expr, ctx, 'db.upsert - conflict_fields must evaluate to a list')
    conflict_fields = [str(field_name) for field_name in conflict_fields_raw]

    if len(conflict_fields) == 0:
        raise ValueError('db.upsert - conflict_fields must not be empty')

    return (ctx, model_class, data, conflict_fields), {}

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
    except KeyError as e:
        raise ValueError(f'db.query - missing arg: {e}')

    has_where = 'where' in expression['args']
    has_fields = 'fields' in expression['args']
    if has_where and has_fields:
        raise ValueError('db.query - args.where and args.fields cannot both be provided')
    if not has_where and not has_fields:
        raise ValueError('db.query - missing arg: where')

    where_expr = expression['args']['where'] if has_where else expression['args']['fields']

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    where = _db_parse_where_conditions(app, where_expr, ctx, 'db.query', legacy_fields=has_fields)

    offset = _resolve_expression_value(app, expression['args']['offset'], ctx) if 'offset' in expression['args'] else 0
    size = _resolve_expression_value(app, expression['args']['size'], ctx) if 'size' in expression['args'] else 25

    kwargs = {}
    include_expr = expression['args'].get('include')
    if include_expr is not None:
        kwargs['include'] = _db_parse_include_spec(app, include_expr, ctx)

    unique_counts_expr = expression['args'].get('unique_counts')
    if unique_counts_expr is not None:
        kwargs['unique_counts'] = _db_parse_unique_counts_specs(app, unique_counts_expr, ctx)

    sort_expr = expression['args'].get('sort')
    if sort_expr is not None:
        kwargs['sort'] = _db_parse_sort_specs(app, sort_expr, ctx)

    return (ctx, model_class, where, offset, size), kwargs

def _db_delete_where_function_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> tuple[tuple, dict]:
    try:
        model_type_expr = expression['args']['model_type']
        where_expr = expression['args']['where']
    except KeyError as e:
        raise ValueError(f'db.delete_where - missing arg: {e}')

    model_type = _resolve_expression_value(app, model_type_expr, ctx)
    model_class = _get_model_class_from_type(app, model_type)
    where = _db_parse_where_conditions(app, where_expr, ctx, 'db.delete_where')

    kwargs = {}
    if 'message' in expression['args']:
        kwargs['message'] = str(_resolve_expression_value(app, expression['args']['message'], ctx))

    return (ctx, model_class, where), kwargs

def _db_project_model_fields(model: Any, field_names: list[str]) -> dict:
    model_data = model._asdict()
    projected = {}
    for field_name in field_names:
        try:
            projected[field_name] = model_data[field_name]
        except KeyError:
            raise ValueError(f'db.include - field not found on included model: {field_name}')
    return projected

def _db_sort_models_by_id(models: list[Any]) -> list[Any]:
    """Sort model rows by ID with numeric ordering when IDs are numeric strings."""
    def _sort_key(model):
        model_id = getattr(model, 'id', None)
        try:
            return int(model_id)
        except (TypeError, ValueError):
            return str(model_id)
    return sorted(models, key=_sort_key)

def _db_resolve_include_for_row(ctx, row: dict, include: dict) -> Any:
    local_value = row.get(include['local_field'])
    if local_value is None:
        return [] if include['cardinality'] == 'many' else None

    if include['foreign_field'] == 'id':
        try:
            joined_model = db_model_read(ctx, include['model_class'], str(local_value))
            joined_rows = [joined_model]
        except NotFoundError:
            joined_rows = []
    else:
        joined_result = db_model_query(ctx, include['model_class'], {include['foreign_field']: {'eq': local_value}}, 0, db_query_batch_size)
        joined_rows = joined_result['items']

    joined_rows = _db_sort_models_by_id(joined_rows)
    projected_rows = [_db_project_model_fields(model, include['fields']) for model in joined_rows]

    if include['cardinality'] == 'many':
        return projected_rows

    return projected_rows[0] if projected_rows else None

def db_read(ctx, model_class, model_id:str, include:dict=None) -> dict:
    try:
        model = db_model_read(ctx, model_class, model_id)
        model_value = model._asdict()
        if include is not None:
            model_value[include['alias']] = _db_resolve_include_for_row(ctx, model_value, include)
        return {'type': 'struct', 'value': model_value}
    except NotFoundError as e:
        raise

def db_create(ctx, model_class, data:dict) -> str:
    model = convert_dict_to_model(model_class, data)
    model = db_model_create(ctx, model_class, model)
    return str(model.id)

def db_patch(ctx, model_class, model_id:str, data:dict) -> dict:
    existing = db_model_read(ctx, model_class, model_id)
    updated_data = existing._asdict()
    updated_data.update(data)
    updated_data['date_created'] = None
    updated_data['date_modified'] = None
    model = convert_dict_to_model(model_class, updated_data)
    saved_model = db_model_update(ctx, model_class, model)
    return {'type': 'struct', 'value': saved_model._asdict()}

def db_upsert(ctx, model_class, data:dict, conflict_fields:list[str]) -> dict:
    model_spec = model_class._model_spec
    db_indexes = model_spec.get('db', {}).get('indexes', [])
    unique_model_fields = model_spec.get('unique_model_fields', [])
    normalized_unique_model_fields = set()
    for field in unique_model_fields:
        if isinstance(field, str):
            normalized_unique_model_fields.add(field)
        elif isinstance(field, dict):
            try:
                normalized_unique_model_fields.add(field['name']['snake_case'])
            except KeyError:
                continue
    has_unique_conflict_index = False
    conflict_set = set(conflict_fields)

    for index in db_indexes:
        if index.get('unique') is True and set(index.get('fields', [])) == conflict_set:
            has_unique_conflict_index = True
            break

    if not has_unique_conflict_index and len(conflict_fields) == 1:
        if conflict_fields[0] in normalized_unique_model_fields:
            has_unique_conflict_index = True

    if not has_unique_conflict_index:
        raise MappValidationError(
            'db.upsert - conflict_fields must match a unique index in model definition',
            {'conflict_fields': 'Must match a unique index in the model definition.'},
        )

    for field_name in conflict_fields:
        if field_name not in data:
            raise MappValidationError(
                f'db.upsert - conflict field missing from data: {field_name}',
                {field_name: 'Conflict field is required in data.'},
            )

    where = {field_name: {'eq': data[field_name]} for field_name in conflict_fields}
    query_result = db_model_query(ctx, model_class, where, 0, db_upsert_conflict_check_size)

    if query_result['total'] == 0:
        model = convert_dict_to_model(model_class, data)
        saved_model = db_model_create(ctx, model_class, model)
    elif query_result['total'] == 1:
        existing = query_result['items'][0]
        updated_data = existing._asdict()
        updated_data.update(data)
        # db_model_update expects timestamp inputs to be unset and handles them automatically.
        updated_data['date_created'] = None
        updated_data['date_modified'] = None
        model = convert_dict_to_model(model_class, updated_data)
        saved_model = db_model_update(ctx, model_class, model)
    else:
        raise MappValidationError(
            'db.upsert - conflict_fields matched multiple rows; expected unique match',
            {'conflict_fields': 'Matched multiple rows; expected one due to unique index.'},
        )

    return {'type': 'struct', 'value': saved_model._asdict()}

def db_unique_counts(ctx, model_class, group_by:str, filters=None) -> list:
    rows = db_model_unique_counts(ctx, model_class, group_by, filters)
    return [{'type': 'struct', 'value': row} for row in rows]

def db_query(ctx, model_class, where:dict, offset:int=0, size:int=25, include:dict=None, unique_counts:list=None, sort:list=None) -> list:
    query_result = db_model_query(ctx, model_class, where, offset, size, sort=sort)

    items = [item._asdict() for item in query_result['items']]
    if include is not None:
        for item in items:
            item[include['alias']] = _db_resolve_include_for_row(ctx, item, include)

    if unique_counts is not None:
        for item in items:
            for unique_count in unique_counts:
                source_value = item.get(unique_count['source_field'])
                if source_value is None:
                    item[unique_count['alias']] = []
                    continue
                item[unique_count['alias']] = db_model_unique_counts(
                    ctx,
                    unique_count['model_class'],
                    unique_count['group_by'],
                    {unique_count['foreign_field']: source_value},
                )
    
    return {
        'type': 'struct',
        'value': {
            'items': items,
            'total': query_result['total']
        }
    }

def db_delete_where(ctx, model_class, where:dict, message:str='Items deleted.') -> dict:
    query_result = db_model_query(ctx, model_class, where, 0, db_query_batch_size)
    for item in query_result['items']:
        db_model_delete(ctx, model_class, item.id)
    return {'type': 'struct', 'value': {'acknowledged': True, 'message': message}}

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

def str_ljust(string:str, width:int, fillchar:str=' ') -> str:
    return string.ljust(width, fillchar)

def str_rjust(string:str, width:int, fillchar:str=' ') -> str:
    return string.rjust(width, fillchar)

def str_center(string:str, width:int, fillchar:str=' ') -> str:
    return string.center(width, fillchar)

def str_strip(string:str, chars:str=None) -> str:
    return string.strip(chars)

def str_rstrip(string:str, chars:str=None) -> str:
    return string.rstrip(chars)

def str_lstrip(string:str, chars:str=None) -> str:
    return string.lstrip(chars)

def str_replace(string:str, old:str, new:str, count:int=-1) -> str:
    if count == -1:
        return string.replace(old, new)
    return string.replace(old, new, count)

def str_re_match(pattern:str, string:str) -> bool:
    return bool(re.match(pattern, string))

def lingo_isclose(a:float, b:float, rel_tol:float=1e-09, abs_tol:float=0.0) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

def lingo_count(source, value) -> int:
    return source.count(value)

def struct_key(object:dict, key_name:str, default_value:Any=None) -> Any:
    # Validate key_name
    if not isinstance(key_name, str) or key_name.startswith('.') or key_name.endswith('.'):
        raise ValueError(f'struct_key - key_name must be a string and must not start or end with a dot: {key_name}')

    keys = key_name.split('.')
    if len(keys) > 10:
        raise ValueError(f'struct_key - key_name exceeds 10 keys: {key_name}')

    current = object
    for key in keys:
        if isinstance(current, dict):
            if key in current:
                current = current[key]
            else:
                if default_value is not None:
                    return default_value
                else:
                    print('STRUCT - MISSING KEY:', key_name, object)
                    raise ValueError(f'struct_key - key not found in struct: {key_name} (missing: {key})')
        elif isinstance(current, list):
            try:
                idx = int(key)
            except Exception:
                raise ValueError(f'struct_key - expected integer index for list access, got: {key} in {key_name}')
            if idx < 0 or idx >= len(current):
                if default_value is not None:
                    return default_value
                else:
                    raise ValueError(f'struct_key - list index out of range: {idx} in {key_name}')
            current = current[idx]
        else:
            raise ValueError(f'struct_key - cannot access key {key} in non-dict/list object (type={type(current).__name__}) for {key_name}')
    return current

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
    'floor': {'func': math.floor, 'args': {'number': {'type': ('int', 'float')}}},
    'ceil': {'func': math.ceil, 'args': {'number': {'type': ('int', 'float')}}},
    'trunc': {'func': math.trunc, 'args': {'number': {'type': ('int', 'float')}}},
    'isclose': {'func': lingo_isclose, 'args': {'a': {'type': 'float'}, 'b': {'type': 'float'}, 'rel_tol': {'type': 'float', 'default': 1e-09}, 'abs_tol': {'type': 'float', 'default': 0.0}}},

    # str #

    'str': {'func': str_convert, 'args': {'object': {'type': 'any'}}},
    'join': {'func': str_join, 'args': {'separator': {'type': 'str'}, 'items': {'type': 'list'}}},
    'concat': {'func': str_concat, 'args': {'items': {'type': 'list'}}},
    'casefold': {'func': lambda string: string.casefold(), 'args': {'string': {'type': 'str'}}},
    'ljust': {'func': str_ljust, 'args': {'string': {'type': 'str'}, 'width': {'type': 'int'}, 'fillchar': {'type': 'str', 'default': ' '}}},
    'rjust': {'func': str_rjust, 'args': {'string': {'type': 'str'}, 'width': {'type': 'int'}, 'fillchar': {'type': 'str', 'default': ' '}}},
    'center': {'func': str_center, 'args': {'string': {'type': 'str'}, 'width': {'type': 'int'}, 'fillchar': {'type': 'str', 'default': ' '}}},
    'strip': {'func': str_strip, 'args': {'string': {'type': 'str'}, 'chars': {'type': 'str', 'default': None}}},
    'rstrip': {'func': str_rstrip, 'args': {'string': {'type': 'str'}, 'chars': {'type': 'str', 'default': None}}},
    'lstrip': {'func': str_lstrip, 'args': {'string': {'type': 'str'}, 'chars': {'type': 'str', 'default': None}}},
    'removeprefix': {'func': lambda string, prefix: string.removeprefix(prefix), 'args': {'string': {'type': 'str'}, 'prefix': {'type': 'str'}}},
    'removesuffix': {'func': lambda string, suffix: string.removesuffix(suffix), 'args': {'string': {'type': 'str'}, 'suffix': {'type': 'str'}}},
    'startswith': {'func': lambda string, prefix: string.startswith(prefix), 'args': {'string': {'type': 'str'}, 'prefix': {'type': 'str'}}},
    'endswith': {'func': lambda string, suffix: string.endswith(suffix), 'args': {'string': {'type': 'str'}, 'suffix': {'type': 'str'}}},
    'replace': {'func': str_replace, 'args': {'string': {'type': 'str'}, 'old': {'type': 'str'}, 'new': {'type': 'str'}, 'count': {'type': 'int', 'default': -1}}},
    're_match': {'func': str_re_match, 'args': {'pattern': {'type': 'str'}, 'string': {'type': 'str'}}},

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
    'count': {'func': lingo_count, 'args': {'source': {'type': ('str', 'list')}, 'value': {'type': ('str', 'int', 'float')}}},

    # sequence ops #

    'map': {'func': map, 'create_args': _indexed_map_function_args},
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
        'invite_user': {'func': invite_user, 'create_args': _invite_user_function_args},
        'is_logged_in': {'func': is_logged_in, 'create_args': _is_logged_in_function_args},
        'current_user': {'func': current_user, 'create_args': _current_user_function_args},
        'logout_user': {'func': logout_user, 'create_args': _logout_user_function_args},
        'delete_user': {'func': delete_user, 'create_args': _delete_user_function_args},
        'drop_sessions': {'func': drop_sessions, 'create_args': _drop_sessions_function_args}
    },

    # com #

    'com': {
        'send_email': {'func': send_email, 'create_args': _send_email_function_args},
        'start_email_verification': {'func': start_email_verification, 'create_args': _start_email_verification_function_args},
        'verify_email_address': {'func': verify_email_address, 'create_args': _verify_email_address_function_args}
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
        'create': {'func': db_create, 'create_args': _db_create_function_args},
        'patch': {'func': db_patch, 'create_args': _db_patch_function_args},
        'upsert': {'func': db_upsert, 'create_args': _db_upsert_function_args},
        'read': {'func': db_read, 'create_args': _db_read_function_args},
        'unique_counts': {'func': db_unique_counts, 'create_args': _db_unique_counts_function_args},
        'query': {'func': db_query, 'create_args': _db_query_function_args},
        'delete_where': {'func': db_delete_where, 'create_args': _db_delete_where_function_args},
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
        elif 'value' in expression:
            result = render_value(app, expression, ctx)
        elif 'self' in expression:
            result = render_self(app, expression, ctx)
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
            except AuthenticationError:
                raise
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
    self_key = expression['self']
    if not isinstance(self_key, str):
        raise ValueError('self - self key must be a string')

    try:
        return ctx.self[self_key]
    except AttributeError:
        try:
            return ctx['self'][self_key]
        except KeyError:
            raise ValueError(f'self - self key not found in context: {self_key}')

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
    
    # optional self key to create local state downstream #
    self_keys = []
    if 'self' in expression:
        try:
            for self_key, self_expr in expression['self'].items():
                ctx.self[self_key] = lingo_execute(app, self_expr, ctx)
                self_keys.append(self_key)
        except AuthenticationError:
            raise
        except Exception as e:
            raise ValueError(f'value - error processing self expression for key: {self_key}') from e
        
    
    # execute based on type #
    
    match _type:
        case 'bool' | 'int' | 'float' | 'str' | 'datetime':
            if isinstance(expression['value'], dict):
                try:
                    result = lingo_execute(app, expression['value'], ctx)
                except Exception as e:
                    raise ValueError('value - error processing expression') from e
            else:
                result = expression
        
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

            result = expression
        
        case 'struct':
            if not isinstance(expression['value'], dict):
                raise ValueError('value - expected struct value')
            
            result_struct = {}
            for field_name, field_value in expression['value'].items():
                if isinstance(field_value, dict):
                    try:
                        result_struct[field_name] = lingo_execute(app, field_value, ctx)
                    except (NotFoundError, MappValidationError, AuthenticationError):
                        raise
                    except Exception as e:
                        raise ValueError(f'value - error processing struct field {field_name}') from e
                else:
                    result_struct[field_name] = field_value
            
            expression['value'] = result_struct
            result = expression
        
        case _:
            raise ValueError(f'value - unsupported type: {_type}')

    for self_key in self_keys:
        del ctx.self[self_key]

    return result
