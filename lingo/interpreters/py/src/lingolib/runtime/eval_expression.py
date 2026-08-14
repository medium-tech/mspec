from typing import Any

from lingolib import symbols
from lingolib.errors import LingoLibError, LingoTypeError

from lingolib.context import (
	LingoContext, 
	LingoRegisteredFunction, 
    LingoRegisteredDefinition, 
	LingoRegisteredValue
)

from lingolib.types import (
	LingoPrimitiveTypes, 
	LingoValue, 
	LingoLanguageError, 
	LingoTypesToPythonTypes, 
	error_to_str, 
	value_to_str,
)

__all__ = [
    'unwrap_value',
    'evaluate_expression',
    'unwrap_expression'
]

#
# types and errors
#

def unwrap_value(ctx, expr:LingoPrimitiveTypes|symbols.L_SYM_value) -> Any:
    if isinstance(expr, (LingoPrimitiveTypes, LingoLanguageError, list, dict)):
        return expr
    elif isinstance(expr, symbols.L_SYM_value):
        if isinstance(expr.value, (LingoPrimitiveTypes, list, dict)):
            return expr.value
        else:
            return unwrap_value(ctx, L_EXPR_value(ctx, expr))
    elif isinstance(expr, LingoValue):
        if isinstance(expr.value, (LingoPrimitiveTypes, list, dict)):
            return expr.value
        else:
            return unwrap_value(ctx, L_EXPR_value(ctx, symbols.L_SYM_value(L_SRC='<unwrap>', type=expr.type, value=expr.value)))
    elif isinstance(expr, (LingoRegisteredFunction, LingoRegisteredDefinition, LingoRegisteredValue)):
        return unwrap_expression(ctx, expr.ast)
    else:
        raise LingoTypeError(f'could not unwrap: {type(expr).__name__}')

class LingoErrorPassThrough(Exception):
    """
    The lingo languge has an error symbol used similarly to Go's error handling, where instead of throwing an exception, a function can return an error value.
    in lingo, if any function/symbol arg is an error it will automatically pass that through as its return value without executing the function/symbol's main logic.
    The only lingo function that will not pass it through is the handle symbol, which converts the error to a string value and returns that.

    But in the python interpreter, sometimes its better to raise and catch exceptions, and for that we use this exception.
    The actual lingo error is passed around as LingoLanguageError which is a NamedTuple,
    These are different than LingoLibError and its subclasses which are used for actual exceptions in the interpreter implementation, and should not be confused with LingoLanguageError.
    """

    def __init__(self, error: LingoLanguageError):
        self.error = error

def raise_error(item: Any) -> Any:
    """useful for iterating over long sequences, to avoid multiple iterations to check for errors"""
    if isinstance(item, LingoLanguageError):
        raise LingoErrorPassThrough(item)
    else:
        return item

#
# execution
#

def evaluate_expression(ctx: LingoContext, expr):
    if isinstance(expr, LingoLanguageError):
        return expr
    else:
        try:
            expr_callable = get_expression_handler(expr.L_SYM_NAME)
        except AttributeError:
            if isinstance(expr, (LingoPrimitiveTypes, LingoValue)):
                return expr
            else:
                raise LingoTypeError(f'expected expression to be symbol, got: {type(expr).__name__}') from None
        
        try:
            return expr_callable(ctx, expr)
        except Exception as e:
            raise LingoLibError(f'error executing expression: {e.__class__.__name__}: {e}')
    
def unwrap_expression(ctx, expr):
    return unwrap_value(ctx, evaluate_expression(ctx, expr))
    
#
# symbol executors
#

# core #

def L_EXPR_get(ctx, symbol:symbols.L_SYM_get):
    # 'state' and lib module namespaces (e.g. 'hello_ns') are supported
    # eventually 'self' and 'params' as well as arbitrary struct expressions
    from_value = unwrap_expression(ctx, symbol.from_)
    if isinstance(from_value, LingoLanguageError):
        return from_value

    # get data source #

    if isinstance(from_value, dict):
        data_source = from_value
        data_key = symbol.field

    elif isinstance(from_value, str):
        if from_value == 'state':
            data_key = symbol.field
            try:
                data_source = ctx.tk.state.values
            except AttributeError as e:
                error_code = 'GET_EXPR_NOT_FOUND'
                error_msg = f'no state context available for {symbol.field!r}'
                ctx.log.error(f'{error_code} - {error_msg}, python exc: {e.__class__.__name__}: {e}')
                return LingoLanguageError(f'{error_code} - {error_msg}', code=error_code)

        elif from_value.startswith('lib'):
            # e.g. get: {field: 'sample_person', from: 'lib.hello_ns'}
            module_name = from_value[4:]
            data_source = ctx.registry.lib
            data_key = f'{module_name}.{symbol.field}'

        else:
            return LingoLanguageError(f'unsupported data source {from_value!r} for get field {symbol.field!r}', code='GET_EXPR_NAME_ERROR')

    else:
        return LingoLanguageError(f'get "from" must resolve to a data source name (str) or a struct (dict), got: {type(from_value).__name__}', code='GET_EXPR_TYPE_ERROR')

    # get field from data source #

    try:
        value = data_source[data_key]
    except (TypeError, AttributeError) as e:
        error_code = 'GET_EXPR_TYPE_ERROR'
        error_msg = f'data source {from_value!r} is wrong type: {type(data_source).__name__!r}'
        ctx.log.error(f'{error_code} - {error_msg}, python exc: {e.__class__.__name__}: {e}')
        return LingoLanguageError(f'{error_code} - {error_msg}', code=error_code)
    
    except KeyError as e:
        error_code = 'GET_EXPR_KEY_ERROR'
        error_msg = f'missing field {symbol.field!r} in {from_value!r}'
        ctx.log.error(f'{error_code} {error_msg}, python exc: {e.__class__.__name__}: {e}')
        return LingoLanguageError(error_msg, code=error_code)

    return value

def L_EXPR_value(ctx, symbol:symbols.L_SYM_value):

    # struct values are stored as a raw dict of primitives, not expression nodes, so there is nothing to unwrap
    if symbol.type == 'struct':
        if not isinstance(symbol.value, dict):
            return LingoLanguageError(f'value type mismatch: expected struct (dict), got {type(symbol.value).__name__!r}', code='TYPE_ERROR')
        return LingoValue(type='struct', value=symbol.value)

    result = unwrap_expression(ctx, symbol.value)
    if isinstance(result, LingoLanguageError):
        return result
    if type(result).__name__ != symbol.type:
        return LingoLanguageError(f'value type mismatch: expected {symbol.type!r}, got {type(result).__name__!r}', code='TYPE_ERROR')

    if symbol.type == 'list':
        verify_element_type = lambda x: type(x).__name__ != symbol.element_type
        if any(verify_element_type(item) for item in result):
            return LingoLanguageError(f'value type mismatch: expected list of {symbol.element_type!r}, got {[type(item).__name__ for item in result]}', code='TYPE_ERROR')
    
    return LingoValue(
        type=symbol.type, 
        value=result
    )

def L_EXPR_error(ctx:LingoContext, symbol:symbols.L_SYM_error):
    if not isinstance(symbol.error, str) or not isinstance(symbol.code, str):
        return LingoLanguageError(f'error and code fields of error symbol must be literal str values', code='TYPE_ERROR')
    else:
        return LingoLanguageError(error=symbol.error, code=symbol.code)
    
def L_EXPR_handle(ctx, symbol:symbols.L_SYM_handle):
    result = evaluate_expression(ctx, symbol.expr)
    
    if isinstance(result, LingoLanguageError):
        return error_to_str(result)
    else:
        return result

def L_EXPR_set(ctx, symbol:symbols.L_SYM_set):
    try:
        data_source, field_name = symbol.name.split('.')
    except ValueError:
        return LingoLanguageError(f'set symbol name must be in the form data_source.field_name, got: {symbol.name!r}', code='SET_EXPR_NAME_ERROR')

    # get data source #

    match data_source:
        case 'state':

            try:
                data = ctx.tk.state.values
            except AttributeError as e:
                error_code = 'SET_EXPR_MISSING_STATE'
                error_msg = f'no state context available for {field_name!r}'
                ctx.log.error(f'{error_code} - {error_msg}, python exc: {e.__class__.__name__}: {e}')
                return LingoLanguageError(f'{error_code} - {error_msg}', code=error_code)
            
        case _:
            return LingoLanguageError(f'unsupported data source "{data_source}" for set: {symbol.name!r}', code='SET_EXPR_NAME_ERROR')

    # evaluate expression #

    value = evaluate_expression(ctx, symbol.value)
    if isinstance(value, LingoLanguageError):
        return value

    # type check #

    primitive_value = unwrap_value(ctx, value)

    if type(primitive_value).__name__ != ctx.tk.state.fields[field_name].type:
        return LingoLanguageError(f'set value type mismatch: expected {ctx.tk.state.fields[field_name].type!r}, got {type(primitive_value).__name__!r}', code='TYPE_ERROR')

    # set and return #
    
    data[field_name] = primitive_value
    
    return value

def L_EXPR_args(ctx, symbol:symbols.L_SYM_args):
    if ctx.registry is None or not ctx.registry.call_args_stack:
        return LingoLanguageError(f'no active call context to resolve arg {symbol.name!r}', code='ARGS_EXPR_MISSING_CONTEXT')

    current_args = ctx.registry.call_args_stack[-1]
    try:
        return current_args[symbol.name]
    except KeyError:
        return LingoLanguageError(f'missing arg {symbol.name!r} in current call context', code='ARGS_EXPR_KEY_ERROR')

def L_EXPR_call(ctx, symbol:symbols.L_SYM_call):
    if ctx.registry is None:
        return LingoLanguageError('no registry context available for call symbol', code='CALL_EXPR_MISSING_REGISTRY')

    call_parts = symbol.func.split('.')
    if len(call_parts) != 2:
        return LingoLanguageError(f'call function must be in the form "<namespace>.<function>", got: {symbol.func!r}', code='CALL_EXPR_NAME_ERROR')

    namespace, func_name = call_parts

    if namespace == 'ops':
        registry, lookup_key = ctx.registry.ops, func_name
    else:
        registry, lookup_key = ctx.registry.lib, symbol.func

    try:
        registered_func = registry[lookup_key]
    except KeyError:
        return LingoLanguageError(f'function {symbol.func!r} not found in registry', code='CALL_EXPR_NOT_FOUND')

    if not isinstance(registered_func, LingoRegisteredFunction):
        return LingoLanguageError(f'{symbol.func!r} is not callable', code='CALL_EXPR_NOT_CALLABLE')

    func_symbol = registered_func.ast

    # evaluate call args #

    try:
        call_args = {arg_name: raise_error(unwrap_expression(ctx, arg_expr)) for arg_name, arg_expr in symbol.args.items()}
    except LingoErrorPassThrough as e:
        
        return e.error

    # apply defaults for any missing args #

    for arg_define in func_symbol.args:
        if arg_define.name not in call_args:
            if arg_define.default is not None:
                call_args[arg_define.name] = unwrap_expression(ctx, arg_define.default)
            else:
                return LingoLanguageError(f'missing required arg {arg_define.name!r} for call {symbol.func!r}', code='CALL_EXPR_MISSING_ARG')

    # execute function body, with call_args bound so "args" symbols inside it can resolve #

    ctx.registry.call_args_stack.append(call_args)
    try:
        return evaluate_expression(ctx, func_symbol.func)
    finally:
        ctx.registry.call_args_stack.pop()

def L_EXPR_validate(ctx, symbol:symbols.L_SYM_validate):
    against = symbol.against

    if isinstance(against, str):
        if ctx.registry is None:
            return LingoLanguageError(f'no registry context available to resolve validate reference {against!r}', code='VALIDATE_EXPR_MISSING_REGISTRY')

        try:
            registered = ctx.registry.lib[against]
        except KeyError:
            return LingoLanguageError(f'validate reference {against!r} not found in registry.lib', code='VALIDATE_EXPR_NOT_FOUND')

        if not isinstance(registered, LingoRegisteredDefinition):
            return LingoLanguageError(f'validate reference {against!r} must resolve to a define, got: {type(registered).__name__}', code='VALIDATE_EXPR_TYPE_ERROR')

        against = registered.ast

    if not isinstance(against, symbols.L_SYM_define):
        return LingoLanguageError(f'validate against must resolve to a define symbol, got: {type(against).__name__}', code='VALIDATE_EXPR_TYPE_ERROR')

    item_value = unwrap_expression(ctx, symbol.item)

    if isinstance(item_value, LingoLanguageError):
        return item_value

    validation_error = _validate_value_against_define(item_value, against)
    if validation_error is not None:
        return LingoLanguageError(validation_error, code='VALIDATE_EXPR_TYPE_ERROR')

    return LingoValue(type=against.type, value=item_value)

def _validate_value_against_define(value, define:symbols.L_SYM_define) -> LingoLanguageError | None:
    """for now this only fully validates struct (and its nested fields); other primitives get a basic type check"""

    if define.type == 'struct':
        if not isinstance(value, dict):
            return LingoLanguageError(f'expected struct, got {type(value).__name__}', code='VALIDATION_ERROR')

        for field_name, field_definition in (define.fields or {}).items():
            if field_name not in value:
                return LingoLanguageError(f'missing field {field_name!r}', code='VALIDATION_ERROR')

            field_error = _validate_value_against_define(value[field_name], field_definition)
            if field_error is not None:
                return LingoLanguageError(f'field {field_name!r}: {field_error}', code='VALIDATION_ERROR')

        # check that there are no extra fields
        extra_fields = set(value.keys()) - set((define.fields or {}).keys())
        if extra_fields:
            return LingoLanguageError(f'extra fields not defined in struct: {", ".join(sorted(extra_fields))}', code='VALIDATION_ERROR')

        return None

    expected_python_type = LingoTypesToPythonTypes.get(define.type)
    if expected_python_type is None:
        return LingoLanguageError(f'unsupported define type: {define.type!r}', code='VALIDATION_ERROR')

    # bool is a subclass of int in python, so guard against a bool value passing an int check and vice versa
    if isinstance(value, bool) != (define.type == 'bool'):
        return LingoLanguageError(f'expected {define.type!r}, got {type(value).__name__}', code='VALIDATION_ERROR')

    if not isinstance(value, expected_python_type):
        return LingoLanguageError(f'expected {define.type!r}, got {type(value).__name__}', code='VALIDATION_ERROR')

    if define.type == 'list':
        element_python_type = LingoTypesToPythonTypes.get(define.element_type)
        if element_python_type is not None:
            for index, item in enumerate(value):
                if not isinstance(item, element_python_type):
                    return LingoLanguageError(f'expected list of {define.element_type!r}, got {type(item).__name__} at index {index}', code='VALIDATION_ERROR')

    return None
    
# comparison #

def L_EXPR_eq(ctx, symbol:symbols.L_SYM_eq):
    try:
        a = raise_error(unwrap_expression(ctx, symbol.a))
        b = raise_error(unwrap_expression(ctx, symbol.b))
    except LingoErrorPassThrough as e:
        return e.error
    
    return LingoValue(type='bool', value=a == b)

# int #

def L_EXPR_int(ctx, symbol:symbols.L_SYM_int):
    try:
        number = raise_error(unwrap_expression(ctx, symbol.number))
        base = raise_error(unwrap_expression(ctx, symbol.base))
    except LingoErrorPassThrough as e:
        return e.error
    
    if isinstance(number, int):
        if base == 10:
            try:
                return LingoValue(type='int', value=number)
            except (TypeError, ValueError) as e:
                return LingoLanguageError(f'cannot convert {number!r} to int: {e}')
        else:
            return LingoLanguageError(f'Must provide number as str to use base other than 10')
    elif isinstance(number, str):
        try:
            return LingoValue(type='int', value=int(number, base=base))
        except (TypeError, ValueError) as e:
            return LingoLanguageError(f'cannot convert {number!r} to int with base {base}: {e}')
    else:
        return LingoLanguageError(f'Number must be int or str, got {type(number).__name__}')
    
def L_EXPR_add(ctx, symbol:symbols.L_SYM_add):
    try:
        a = raise_error(unwrap_expression(ctx, symbol.a))
        b = raise_error(unwrap_expression(ctx, symbol.b))
    except LingoErrorPassThrough as e:
        return e.error

    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return LingoValue(
            type='int' if isinstance(a, int) and isinstance(b, int) else 'float', 
            value=a + b
        )
    else:
        return LingoLanguageError(f'args must be int or float for add symbol, got a: {type(a).__name__} and b: {type(b).__name__}', code='TYPE_ERROR')

# str #

def L_EXPR_str(ctx, symbol:symbols.L_SYM_str):

    primitive = unwrap_expression(ctx, symbol.object)

    if isinstance(primitive, LingoLanguageError):
        return primitive

    else:
        return LingoValue(type='str', value=value_to_str(primitive))

def L_EXPR_concat(ctx, symbol:symbols.L_SYM_concat):
    try:
        items = [raise_error(unwrap_expression(ctx, item)) for item in symbol.items]
    except LingoErrorPassThrough as e:
        return e.error
    
    try:
        return LingoValue(type='str', value=''.join(items))
    except TypeError as e:
        ctx.log.debug(f'error concatenating items: {e.__class__.__name__}: {e}')
        return LingoLanguageError(f'all items for concat symbol must be str')
    
def L_EXPR_join(ctx, symbol:symbols.L_SYM_join):
    try:
        items = [raise_error(unwrap_expression(ctx, item)) for item in symbol.items]
        separator = raise_error(unwrap_expression(ctx, symbol.separator))
    except LingoErrorPassThrough as e:
        return e.error
    
    try:
        return LingoValue(type='str', value=separator.join(items))
    
    except TypeError as e:
        ctx.log.debug(f'error joining items: {e.__class__.__name__}: {e}')
        return LingoLanguageError(f'separator and all items for join symbol must be str')


EXPRESSION_HANDLERS = {
    'get': L_EXPR_get,
    'set': L_EXPR_set,
    'args': L_EXPR_args,
    'call': L_EXPR_call,
    'validate': L_EXPR_validate,
    'value': L_EXPR_value,
    'error': L_EXPR_error,
    'handle': L_EXPR_handle,
    'eq': L_EXPR_eq,
    'int': L_EXPR_int,
    'add': L_EXPR_add,
    'str': L_EXPR_str,
    'concat': L_EXPR_concat,
    'join': L_EXPR_join,
}


def get_expression_handler(sym_name: str):
    try:
        return EXPRESSION_HANDLERS[sym_name]
    except KeyError:
        raise LingoLibError(f'unsupported expression symbol: {sym_name!r}')