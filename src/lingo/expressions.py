from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, date
from random import randint
from typing import Any, Optional

lingo_function_lookup = {
    # built-in functions #
    'bool': {'func': bool, 'args': {'object': {'type': Any}}},

    # standard library functions #
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

    @classmethod
    def init(cls, spec: dict, **params) -> 'LingoApp':
        instance = cls(spec=deepcopy(spec), params=params, state={}, buffer=[])

        for arg_name in params.keys():
            if arg_name not in instance.spec['params']:
                raise ValueError(f'argument {arg_name} not defined in spec')

        return lingo_update_state(instance)


def lingo_update_state(app:LingoApp, ctx: Optional[dict]=None) -> None:
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
                breakpoint()
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
        else:
            return render_element(app, expression, ctx)
    else:
        return expression
    
# high level render #

def render_document(app:LingoApp, ctx:Optional[dict]=None) -> list[dict]:
    app.buffer = []
    for n, element in enumerate(app.spec['document']):
        try:
            app.buffer.append(render_element(app, element, ctx))
        except ValueError as e:
            raise ValueError(f'Render error - document {n} - {e}')
        except Exception as e:
            raise ValueError(f'Render error - document {n} - {e.__class__.__name__}{e}')
    return app.buffer

def render_element(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:

    if 'block' in element:
        return render_block(app, element, ctx)
    elif 'lingo' in element:
        return render_lingo(app, element, ctx)
    elif 'branch' in element:
        return render_branch(app, element, ctx)
    elif 'switch' in element:
        return render_switch(app, element, ctx)
    else:
        return element

def render_block(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    elements = []
    for n, child_element in enumerate(element['block']):
        try:
            elements.append(render_element(app, child_element, ctx))
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
                return lingo_execute(app, then, ctx)
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
                return render_element(app, case['then'], ctx)
        except Exception as e:
            raise ValueError(f'switch - error processing case') from e
    
    return render_element(app, default, ctx)
    
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
        value = app.state[field_name]
    except KeyError:
        breakpoint()
        raise ValueError(f'state - field not found: {field_name}')
    
    # return #
    
    if isinstance(value, dict):
        return value
    else:
        return {'text': str(value)}

# expressions #

def render_lingo(app:LingoApp, element: dict, ctx:Optional[dict]=None) -> None:
    result = lingo_execute(app, element['lingo'], ctx)
    _type = type(result)
    if _type == str:
        return {'text': result}
    elif _type == int or _type == float or _type == bool:
        return {'text': str(result)}
    elif _type == datetime:
        return {'text': result.isoformat()}
    elif _type == dict:
        return result
    else:
        raise ValueError(f'lingo - invalid result type: {_type}')

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
        args = expression['args']
    except KeyError:
        args = {}

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
    for arg_name, arg_value in args.items():
        try:
            arg_type = args_def[arg_name]['type']
        except KeyError:
            raise ValueError(f'call - unknown arg: {arg_name}')
        if not isinstance(arg_value, arg_type):
            raise ValueError(f'call - arg {arg_name} - expected type {arg_type}, got {arg_value.__class__.__name__}')

    return function(**args)

        
example_spec = {

    "params": {
        "first_visit": {"type": "bool", "default": False}
    },

    "state": {
        "greeting": {
            "type": "str",
            "default": "",
            "calc": {
                "branch": [
                    {"if": {"params": {"first_visit": {}}}, "then": "Welcome in, "},
                    {"else": "Welcome back, "}
                ]
            }
        },
        "n": {
            "type": "int",
            "default": 0
        },
        "name": {
            "type": "str",
            "default": ""
        }
    },

    "ops": {
        "randomize_number": {
            "args": {"max": {"type": "int"}},
            "func":{
                "set": {"state": {"n": {}}},
                "to": {"call": "random.randint", "args": {"a": 0, "b": {"args": "max"}}}
            }
        }
    },

    "document": [
        {"heading": {"text": "Example document"}, "level": 1},
        {"block": [
            {"text": "The current date and time is "},
            {"lingo": {"call": "datetime.now"}},
            {"text": "."},
            {"break": 1},

            {"text": "Please tell us your name: "},
            {"input": {"type": "text"}, "state": {"name": {}}},
            {"break": 1},

            {"text": "Here's a random number: "},
            {"lingo": {"state": {"n": {}}}},
            {"text": "."},
            {"break": 1},
            
            {"button": {"op": {"randomize_number": {"max": 100}}}, "text": "Randomize"},
            {"break": 1},

            {"lingo": {"state": {"greeting": {}}}},
            {"branch": [
                {"if": {"call": "random.randint", "args": {"a": 0, "b": 1}}, "then": {"text": "Silly person"}},
                {"elif": {"state": {"name": {"ne": ""}}}, "then": {"lingo": {"state": {"name": {}}}}},
                {"else": {"text": "Unknown person"}}
            ]},
            {"text": "!"},
            {"break": 2},

            {"text": " Happy "},

            {"switch": {
                "expression": {"call": "current.weekday"},
                "cases": [
                    {"case": 0, "then": {"text": "Monday"}},
                    {"case": 1, "then": {"text": "Tuesday"}},
                    {"case": 2, "then": {"text": "Wednesday"}},
                    {"case": 3, "then": {"text": "Thursday"}},
                    {"case": 4, "then": {"text": "Friday"}},
                ],
                "default": {"text": "Weekend"}
            }},

            {"text": "!"},
            {"break": 1},

            {"text": "This is the culmination of many late nights."},
            {"link": "https://shop.coavacoffee.com/cdn/shop/files/RayosDelSol_Retail_drip_1_680x@2x.png?v=1718728683", "text": "coffee, yum, yum"},
            {"text": "well anyway, enjoy!"},
            {"link": "https://miro.medium.com/v2/resize:fit:1152/format:webp/1*Cvj9qvbKh1LmLSGEwwwZCQ.jpeg"}
        ]}
    ]

}