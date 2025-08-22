import operator

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from random import randint
from typing import Any, Optional

datetime_format_str = '%Y-%m-%dT%H:%M:%S'

lingo_function_lookup = {
    'bool': {'func': bool, 'args': {'object': {'type': Any}}},
    'not': {'func': operator.not_, 'args': {'object': {'type': Any}}},
    'neg': {'func': operator.neg, 'args': {'object': {'type': Any}}},

    'and': {'func': operator.and_, 'args': {'a': {'type': Any}, 'b': {'type': Any}}},
    'or': {'func': operator.or_, 'args': {'a': {'type': Any}, 'b': {'type': Any}}},
    
    'add': {'func': operator.add, 'args': {'a': {'type': (int, float)}, 'b': {'type': (int, float)}}},
    'sub': {'func': operator.sub, 'args': {'a': {'type': (int, float)}, 'b': {'type': (int, float)}}},
    'mul': {'func': operator.mul, 'args': {'a': {'type': (int, float)}, 'b': {'type': (int, float)}}},
    'div': {'func': operator.truediv, 'args': {'a': {'type': (int, float)}, 'b': {'type': (int, float)}}},
    'pow': {'func': operator.pow, 'args': {'a': {'type': (int, float)}, 'b': {'type': (int, float)}}},

    'eq': {'func': operator.eq, 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},
    'ne': {'func': lambda a, b: operator.ne(a, b), 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},
    'lt': {'func': operator.lt, 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},
    'le': {'func': operator.le, 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},
    'gt': {'func': operator.gt, 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},
    'ge': {'func': operator.ge, 'args': {'a': {'type': (int, float, str)}, 'b': {'type': (int, float, str)}}},

    'current': {
        'weekday': {'func': lambda: datetime.now().weekday(), 'args': {}}
    },
    'datetime': {
        'now': {'func': datetime.now, 'args': {}}
    },
    'random': {
        'randint': {'func': randint, 'args': {'a': {'type': int}, 'b': {'type': int}}}
    }
}

@dataclass
class LingoApp:
    spec: dict[str, dict]
    params: dict[str, Any]
    state: dict[str, Any]
    buffer: list[dict]


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
                    if value['type'] != value['default'].__class__.__name__:
                        raise ValueError(f'state - {key} - default value type mismatch')
                    app.state[key] = value['default']
                except KeyError:
                    raise ValueError(f'state - {key} - missing default value')
        else:
            new_value = lingo_execute(app, calc, ctx)
            if value['type'] != new_value.__class__.__name__:
                raise ValueError(f'state - {key} - expression returned type: ' + new_value.__class__.__name__)
            app.state[key] = new_value

    return app

def lingo_execute(app:LingoApp, expression:Any, ctx:Optional[dict]=None) -> Any:
    """
    Run the expression and return the result.
    :param
        expression: dict - The expression to run."
    :return: Any - The result of the expression."
    """
    if isinstance(expression, dict):
        if 'set' in expression:
            return render_set(app, expression, ctx)
        elif 'state' in expression:
            return render_state(app, expression, ctx)
        elif 'params' in expression:
            return render_params(app, expression, ctx)
        elif 'op' in expression:
            return render_op(app, expression, ctx)
        elif 'call' in expression:
            return render_call(app, expression, ctx)
        elif 'block' in expression:
            return render_block(app, expression, ctx)
        elif 'lingo' in expression:
            return render_lingo(app, expression, ctx)
        elif 'branch' in expression:
            return render_branch(app, expression, ctx)
        elif 'switch' in expression:
            return render_switch(app, expression, ctx)
        elif 'heading' in expression:
            # heading is a special case for rendering headings
            return render_heading(app, expression, ctx)
        elif 'args' in expression:
            return render_args(app, expression, ctx)
        else:
            # print('warning - unrecognized expression type:', expression)
            return expression
    else:
        return expression
    
# high level render #

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

# control flow #

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
            condition = lingo_execute(app, expr, ctx)
        except Exception as e:
            raise ValueError(f'branch {n} - error processing condition') from e

        if condition:
            try:
                value = lingo_execute(app, then, ctx)
                return value
            except Exception as e:
                raise ValueError(f'branch {n} - error processing then expression') from e

    raise ValueError(f'unvalid branch expression')

def render_switch(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> None:
    try:
        switch = expression['switch']
        expression = switch['expression']
        cases = switch['cases']
        default = switch['default']
    except KeyError as e:
        raise ValueError(f'switch - missing key: {e}')
    
    if len(cases) == 0:
        raise ValueError(f'switch - must have at least one case')

    try:
        value = lingo_execute(app, expression, ctx)
    except Exception as e:
        raise ValueError(f'switch - error processing expression') from e

    for case in cases:
        try:
            if value == case['case']:
                return lingo_execute(app, case['then'], ctx)
        except Exception as e:
            raise ValueError(f'switch - error processing case') from e
    
    return lingo_execute(app, default, ctx)
    
# state and input #

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
        value = app.params[field_name]
    except KeyError:
        try:
            value = param_def['default']
        except KeyError:
            raise ValueError(f'params - missing value for field: {field_name}')
        
    if value.__class__.__name__ != param_def['type']:
        raise ValueError(f'params - value type mismatch: {param_def["type"]} != {value.__class__.__name__}')
    
    # return value #
    
    return value

def render_set(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> None:
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
        value = lingo_execute(app, value_expr, ctx)
    except Exception as e:
        raise ValueError('set - error processing to expression') from e
    
    if value.__class__.__name__ != field_type:
        raise ValueError(f'set - value type mismatch: {field_type} != {value.__class__.__name__}')
    
    app.state[field_name] = value

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

# expressions #

def render_lingo(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    result = lingo_execute(app, element['lingo'], ctx)
    _type = type(result)
    if _type == str:
        return {'text': result}
    elif _type == int or _type == float or _type == bool:
        return {'text': str(result)}
    elif _type == datetime:
        return {'text': result.strftime(datetime_format_str)}
    elif _type == dict:
        return result
    else:
        raise ValueError(f'lingo - invalid result type: {_type}')
    
def render_heading(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> dict:
    
    try:
        if not 1 <= element['level'] <= 6:
            raise ValueError('heading - level must be between 1 and 6')
    except KeyError:
        raise ValueError('heading - missing level key')
    
    try:
        heading = lingo_execute(app, element['heading'], ctx)
    except Exception as e:
        raise ValueError('heading - error processing heading expression') from e
    
    try:
        heading_text = heading['text']
    except KeyError:
        if isinstance(heading, str):
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
            function = lingo_function_lookup[name_split[0]]['func']
            args_def = lingo_function_lookup[name_split[0]].get('args', {})
        else:
            function = lingo_function_lookup[name_split[0]][name_split[1]]['func']
            args_def = lingo_function_lookup[name_split[0]][name_split[1]].get('args', {})
    except KeyError as func_name:
        raise ValueError(f'call - undefined func: {func_name}')
        
    # validate args #
    rendered_args = {}
    for arg_name, arg_expression in _args.items():
        try:
            arg_type = args_def[arg_name]['type']
        except KeyError:
            raise ValueError(f'call - unknown arg: {arg_name}')
        
        value = lingo_execute(app, arg_expression, ctx)
        if arg_type is not Any:
            if not isinstance(value, arg_type):
                breakpoint()
                raise ValueError(f'call - arg {arg_name} - expected type {arg_type}, got {value.__class__.__name__}')
        rendered_args[arg_name] = value

    # Check if function is from operator module or built-in and needs positional args
    if (hasattr(function, '__module__') and function.__module__ == '_operator') or \
       (hasattr(function, '__module__') and function.__module__ == 'builtins'):
        # For operator and built-in functions, convert to positional arguments in the order defined
        args_list = []
        for arg_name in args_def.keys():
            if arg_name in rendered_args:
                args_list.append(rendered_args[arg_name])
            else:
                raise ValueError(f'call - missing required arg: {arg_name}')
        return function(*args_list)
    else:
        return function(**rendered_args)

def render_args(app:LingoApp, expression: dict, ctx:Optional[dict]=None) -> Any:
    arg_name = expression['args']
    try:
        return ctx[arg_name]
    except KeyError:
        raise ValueError(f'args - undefined arg: {arg_name}')
