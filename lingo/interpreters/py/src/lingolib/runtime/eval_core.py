from lingolib.errors import LingoLibError, LingoRuntimeError
from lingolib.symbols import ExpressionSymbols

__all__ = [
	'raise_runtime_error'
]


def raise_runtime_error(symbol: ExpressionSymbols, message: str):
	"""
	raise a LingoRuntimeError with the given message and symbol
	"""
	new_msg = f'{message}'
	
	new_msg += f' {symbol.L_SYM_NAME}'
	if symbol.L_FILE:
		new_msg += f' in {symbol.L_FILE}'
	if symbol.L_LINE >= 0:
		new_msg += f' at line {symbol.L_LINE}~ish'

	raise LingoRuntimeError(new_msg)
