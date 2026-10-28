from lingolib.context import LingoContext
from lingolib.errors import LingoRuntimeError
from lingolib.symbols import ExpressionSymbols, L_SYM_define, L_SYM_params

from lingolib.runtime.eval_expression import unwrap_expression
from getpass import getpass

__all__ = [
	'DEFAULT_HOST',
	'DEFAULT_PORT',
	'DEFAULT_SERVER_PROCESSES',
	'DEFAULT_MAX_BODY_BYTES',
	'DEFAULT_LOG_MAX_SIZE',
	'DEFAULT_DB_FILE',
	'DEFAULT_LIST_LIMIT',
	'MAX_LIST_LIMIT',

	'raise_runtime_error',

	'CLIHelpMenuRequested',
	'parse_cli_bool',
	'convert_cli_value',
	'parse_cli_params',
	'create_help_string',
	'prompt_cli_user_for_param'
]

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
DEFAULT_SERVER_PROCESSES = 1
DEFAULT_MAX_BODY_BYTES = 1_048_576	# ~1MB
DEFAULT_LOG_MAX_SIZE = 104_857_600	# ~100MB
DEFAULT_DB_FILE = 'lingo.db'
DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 1000


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

#
# cli helpers
#

CLI_BOOL_TRUE_VALUES = {'1', 't', 'true', 'y', 'yes'}
CLI_BOOL_FALSE_VALUES = {'0', 'f', 'false', 'n', 'no'}

class CLIHelpMenuRequested(Exception):
	pass

def parse_cli_bool(field_name: str, raw_value: str) -> bool:
	normalized = raw_value.lower()
	if normalized in CLI_BOOL_TRUE_VALUES:
		return True
	elif normalized in CLI_BOOL_FALSE_VALUES:
		return False
	else:
		raise LingoRuntimeError(f'invalid bool value for param {field_name!r}: {raw_value!r}')

def convert_cli_value(field_name: str, field_type: str, raw_value: str):
	match field_type:
		case 'bool':
			return parse_cli_bool(field_name, raw_value)
		case 'int':
			try:
				return int(raw_value)
			except ValueError:
				raise LingoRuntimeError(f'invalid int value for param {field_name!r}: {raw_value!r}') from None
		case 'float':
			try:
				return float(raw_value)
			except ValueError:
				raise LingoRuntimeError(f'invalid float value for param {field_name!r}: {raw_value!r}') from None
		case 'str':
			return raw_value
		case _:
			raise LingoRuntimeError(f'param {field_name!r} has unsupported type for CLI parsing: {field_type!r}')

def parse_cli_params(cli_args: list[str]) -> tuple[dict[str, str], bool]:
	"""parse --field-name value pairs from the CLI args following the exe spec path

	returns a tuple containing a dict and a bool
		- dict[str, str]: mapping of field names to raw CLI values
		- bool: true if interactive mode is enabled
	
	"""

	raw_values = {}
	index = 0
	input_len = len(cli_args)
	interactive = False

	while index < input_len:

		flag = cli_args[index]

		# special flags #

		if flag == '--help':
					raise CLIHelpMenuRequested()
		
		if flag in ('-i', '--interactive'):
			interactive = True
			index += 1
			continue

		# param field flags #

		if not flag.startswith('--') or len(flag) < 3:
			raise LingoRuntimeError(f'expected params flag beginning with --, got: {flag!r}') from None

		field_name = flag[2:].replace('-', '_')

		try:
			raw_values[field_name] = cli_args[index + 1]
		except IndexError:
			raise LingoRuntimeError(f'missing value for param CLI flag: {flag!r}') from None

		index += 2

	return raw_values, interactive

def create_help_string(ctx: LingoContext, params: L_SYM_params) -> str:
	headers = ('param name', 'cli arg', 'type', 'default', 'description')

	rows = []
	for field_name, field_def in params.fields.items():
		cli_arg = f'--{field_name.replace("_", "-")}'
		default = str(unwrap_expression(ctx, field_def.default)) if field_def.default is not None else ''
		rows.append((field_name, cli_arg, field_def.type, default, field_def.description))

	widths = [
		max(len(headers[col]), *(len(row[col]) for row in rows)) if rows else len(headers[col])
		for col in range(len(headers))
	]

	def format_row(row):
		return '\t' + '  '.join(cell.ljust(width) for cell, width in zip(row, widths))

	help_lines = ['Params:\n', format_row(headers), format_row(('-' * width for width in widths))]
	help_lines.extend(format_row(row) for row in rows)
	return '\n'.join(help_lines)

def prompt_cli_user_for_param(field_name: str, field_def: L_SYM_define) -> any:
	while True:
		print(f'Field {field_name} ({field_def.type})')
		print(f'\tDescription: {field_def.description}')

		if field_def.secure:
			raw_value = getpass(f'Enter value (secure): ')
		else:
			raw_value = input(f'Enter value: ')

		try:
			return convert_cli_value(field_name, field_def.type, raw_value)
		except LingoRuntimeError as e:
			print(f'Invalid value: {e.__class__.__name__}: {e}')

