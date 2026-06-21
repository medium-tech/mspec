from typing import Any

from lingolib import symbols
from lingolib.context import LingoContext
from lingolib.errors import LingoError, LingoTypeError
from lingolib.types import expression, LingoPrimitiveTypes, LingoLiteralTypes


def execute_expression(ctx: LingoContext, expr):
    try:
        expr_callable = globals()[f'L_EXPR_{expr.L_SYM_NAME}']
    except AttributeError:
        if isinstance(expr, LingoPrimitiveTypes):
            return expr
        # elif isinstance(expr, list):
        #     return [execute_expression(ctx, item) for item in expr]
        else:
            raise LingoTypeError(f'expected expression to be symbol, got: {type(expr).__name__}') from None
    except KeyError:
        raise LingoError(f'unsupported expression symbol: {expr.L_SYM_NAME!r}')
    
    try:
        return expr_callable(ctx, expr)
    except Exception as e:
        raise LingoError(f'error executing expression: {e.__class__.__name__}: {e}')
    
def unwrap_value(ctx, expr:LingoPrimitiveTypes|symbols.L_SYM_value) -> Any:
    if isinstance(expr, LingoPrimitiveTypes):
        return expr
    elif isinstance(expr, symbols.L_SYM_value):
        if isinstance(expr.value, LingoPrimitiveTypes):
            return expr.value
        else:
            return unwrap_value(ctx, L_EXPR_value(ctx, expr.value))
    else:
        raise LingoTypeError(f'could not unwrap: {type(expr).__name__}')
    
#
# expression executors
#

def L_EXPR_value(ctx, symbol:symbols.L_SYM_value):
    return symbols.L_SYM_value(
        type=symbol.type, 
        value=unwrap_value(ctx, execute_expression(ctx, symbol.value))
    )

def L_EXPR_str(ctx, symbol:symbols.L_SYM_str):
    primitive = unwrap_value(ctx, symbol.object)
    if isinstance(primitive, bool):
        return 'true' if primitive else 'false'
    else:
        return str(primitive)

def L_EXPR_concat(ctx, symbol:symbols.L_SYM_concat):
    return ''.join(unwrap_value(ctx, execute_expression(ctx, item)) for item in symbol.items)