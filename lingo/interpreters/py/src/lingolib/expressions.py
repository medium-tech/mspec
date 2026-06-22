from typing import Any

from lingolib import symbols
from lingolib.context import LingoContext
from lingolib.errors import LingoLibError, LingoTypeError
from lingolib.types import expression, LingoPrimitiveTypes, LingoLiteralTypes, LingoValue, LingoLanguageError


# class LingoErrorPassThrough(Exception):
#     """
#     The lingo languge has an error symbol used similarly to Go's error handling, where instead of throwing an exception, a function can return an error value.
#     in lingo, if any function/symbol arg is an error it will automatically pass that through as its return value without executing the function/symbol's main logic.
#     The only lingo function that will not pass it through is the handle symbol, which converts the error to a string value and returns that.

#     But in the python interpreter, we actually use exception throwing to implement this error pass through behavior from function to function.
#     This exception class is used to accomplish that. The actual lingo error is passed around as LingoLanguageError which is a NamedTuple,
#     These are different than LingoLibError and its subclasses which are used for actual exceptions in the interpreter implementation, and should not be confused with LingoLanguageError.
#     """

#     def __init__(self, error: LingoLanguageError):
#         self.error = error

def get_language_error(errors: list[Any]) -> LingoLanguageError | None:
    for error in errors:
        if isinstance(error, LingoLanguageError):
            return error
    return None

def execute_expression(ctx: LingoContext, expr):
    if isinstance(expr, LingoLanguageError):
        return expr
    else:
        try:
            expr_callable = globals()[f'L_EXPR_{expr.L_SYM_NAME}']
        except AttributeError:
            if isinstance(expr, (LingoPrimitiveTypes, LingoValue)):
                return expr
            else:
                raise LingoTypeError(f'expected expression to be symbol, got: {type(expr).__name__}') from None
        except KeyError:
            raise LingoLibError(f'unsupported expression symbol: {expr.L_SYM_NAME!r}')
        
        try:
            return expr_callable(ctx, expr)
        except Exception as e:
            raise LingoLibError(f'error executing expression: {e.__class__.__name__}: {e}')
    
def unwrap_value(ctx, expr:LingoPrimitiveTypes|symbols.L_SYM_value) -> Any:
    if isinstance(expr, (LingoPrimitiveTypes, LingoLanguageError)):
        return expr
    elif isinstance(expr, symbols.L_SYM_value):
        if isinstance(expr.value, LingoPrimitiveTypes):
            return expr.value
        else:
            return unwrap_value(ctx, L_EXPR_value(ctx, expr.value))
    elif isinstance(expr, LingoValue):
        if isinstance(expr.value, LingoPrimitiveTypes):
            return expr.value
        else:
            return unwrap_value(ctx, L_EXPR_value(ctx, symbols.L_SYM_value(type=expr.type, value=expr.value)))
    else:
        raise LingoTypeError(f'could not unwrap: {type(expr).__name__}')
    
def unwrap_expression(ctx, expr):
    return unwrap_value(ctx, execute_expression(ctx, expr))
    
#
# expression executors
#

def L_EXPR_value(ctx, symbol:symbols.L_SYM_value):

    result = unwrap_expression(ctx, symbol.value)
    if isinstance(result, LingoLanguageError):
        return result
    else:
        return LingoValue(
            type=symbol.type, 
            value=result
        )

def L_EXPR_error(ctx, symbol:symbols.L_SYM_error):
    if not isinstance(symbol.error, str) or not isinstance(symbol.code, str):
        return LingoLanguageError(f'error and code fields of error symbol must be literal str values', code='TYPE_ERROR')
    else:
        return LingoLanguageError(error=symbol.error, code=symbol.code)
    
def L_EXPR_handle(ctx, symbol:symbols.L_SYM_handle):
    result = execute_expression(ctx, symbol.expr)
    
    if isinstance(result, LingoLanguageError):
        return f'ERROR :: {result.code} {result.error}'
    else:
        return result
    
# comparison

def L_EXPR_eq(ctx, symbol:symbols.L_SYM_eq):

    a = unwrap_expression(ctx, symbol.a)
    b = unwrap_expression(ctx, symbol.b)
    
    error = get_language_error([a, b])
    if error:
        return error
    else:
        return a == b

# int

def L_EXPR_int(ctx, symbol:symbols.L_SYM_int):

    number = unwrap_expression(ctx, symbol.number)
    base = unwrap_expression(ctx, symbol.base)

    error = get_language_error([number, base])
    if error:
        return error

    elif isinstance(number, int):
        if base == 10:
            try:
                return int(number)
            except (TypeError, ValueError) as e:
                return LingoLanguageError(f'cannot convert {number!r} to int: {e}')
        else:
            return LingoLanguageError(f'Must provide number as str to use base other than 10')
    elif isinstance(number, str):
        try:
            return int(number, base=base)
        except (TypeError, ValueError) as e:
            return LingoLanguageError(f'cannot convert {number!r} to int with base {base}: {e}')
    else:
        return LingoLanguageError(f'Number must be int or str, got {type(number).__name__}')
    
def L_EXPR_add(ctx, symbol:symbols.L_SYM_add):

    a = unwrap_expression(ctx, symbol.a)
    b = unwrap_expression(ctx, symbol.b)
    error = get_language_error([a, b])

    if error:
        return error
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b
    else:
        return LingoLanguageError(f'args must be int or float for add symbol, got a: {type(a).__name__} and b: {type(b).__name__}', code='TYPE_ERROR')

# str

def L_EXPR_str(ctx, symbol:symbols.L_SYM_str):

    primitive = unwrap_expression(ctx, symbol.object)

    if isinstance(primitive, LingoLanguageError):
        return primitive
    elif isinstance(primitive, bool):
        result = 'true' if primitive else 'false'
    else:
        result = str(primitive)

    return LingoValue(type='str', value=result)

def L_EXPR_concat(ctx, symbol:symbols.L_SYM_concat):
    
    items = [unwrap_expression(ctx, item) for item in symbol.items]
    error = get_language_error(items)
    if error:
        return error
    try:
        return LingoValue(type='str', value=''.join(items))
    except TypeError as e:
        ctx.log.error(f'error concatenating items: {e.__class__.__name__}: {e}')
        return LingoLanguageError(f'all items for concat symbol must be str')