import json

from lingolib.context import LingoContext
from lingolib.errors import LingoRuntimeError
from lingolib.symbols import ExpressionSymbols, L_SYM_define, L_SYM_params

from lingolib.runtime.eval_expression import unwrap_expression
from getpass import getpass
from typing import NamedTuple

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
	'ParamsCLIInput',
	'parse_cli_bool',
	'convert_cli_value',
	'parse_params_cli_args',
	'parse_param_assignments',
	'parse_param_json',
	'format_key_values',
	'describe_defines',
	'create_params_help',
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
JSON_PARAM_TYPES = {'bool': bool, 'int': int, 'float': float, 'str': str}

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

class ParamsCLIInput(NamedTuple):
	"""raw param input from the CLI, shared by the exe, display and client commands"""

	request_body: str | None = None			# --json
	assignments: list[str] | None = None	# --params name=value ...
	interactive: bool = False				# -i

def parse_params_cli_args(cli_args: list[str]) -> ParamsCLIInput:
	"""parse --json, --params name=value [...] and -i from the CLI args following the spec path"""

	request_body = None
	assignments = None
	interactive = False
	index = 0
	input_len = len(cli_args)

	while index < input_len:
		flag = cli_args[index]

		match flag:
			case '--help' | '-h':
				raise CLIHelpMenuRequested()

			case '-i':
				if interactive:
					raise LingoRuntimeError('-i may only be specified once')
				interactive = True
				index += 1

			case '--params':
				if assignments is not None:
					raise LingoRuntimeError('--params may only be specified once')
				assignments = []
				index += 1
				while index < input_len and not cli_args[index].startswith('-'):
					assignments.append(cli_args[index])
					index += 1

			case '--json':
				if request_body is not None:
					raise LingoRuntimeError('--json may only be specified once')
				if index + 1 >= input_len:
					raise LingoRuntimeError('--json requires a value')
				request_body = cli_args[index + 1]
				index += 2

			case _:
				raise LingoRuntimeError(f'unknown params option: {flag!r}; use --json, --params name=value [...] or -i')

	if assignments == [] and not interactive:
		raise LingoRuntimeError('--params requires at least one name=value')
	if request_body is not None and (assignments is not None or interactive):
		raise LingoRuntimeError('--json cannot be combined with --params or -i')

	return ParamsCLIInput(request_body, assignments, interactive)

def parse_param_assignments(
	definitions: dict[str, L_SYM_define],
	owner: str,
	assignments: list[str],
	interactive: bool,
) -> dict:
	"""convert name=value assignments, then prompt for params that are missing and have no default

	defaults are not applied here, callers decide whether to apply them (the client leaves that to the server)
	"""

	parsed = {}

	# parse assignments from cli #

	for assignment in assignments:
		if '=' not in assignment:
			raise LingoRuntimeError(f'parameter must use name=value format, got {assignment!r}')

		name, raw_value = assignment.split('=', 1)
		if not name:
			raise LingoRuntimeError(f'parameter name cannot be empty: {assignment!r}')

		if name in parsed:
			raise LingoRuntimeError(f'parameter specified more than once: {name!r}')
		try:
			field_type = definitions[name].type
		except KeyError:
			raise LingoRuntimeError(f'unknown parameter for {owner}: {name!r}') from None

		parsed[name] = convert_cli_value(name, str(field_type), raw_value)

	# prompt for missing params #

	if interactive:
		for name, definition in definitions.items():
			if name not in parsed and definition.default is None:
				parsed[name] = prompt_cli_user_for_param(name, definition)

	return parsed

def parse_param_json(definitions: dict[str, L_SYM_define], owner: str, raw_json: str) -> dict:
	"""parse a --json object and strictly check its keys and value types against the definitions"""

	try:
		data = json.loads(raw_json)
	except json.JSONDecodeError as e:
		raise LingoRuntimeError(f'invalid JSON request body: {e}') from None

	if not isinstance(data, dict):
		raise LingoRuntimeError('--json must contain a JSON object')

	for name, value in data.items():
		if not isinstance(name, str):
			raise LingoRuntimeError(f'JSON keys must be strings: {name!r}')
		
		try:
			field_type = str(definitions[name].type)
		except KeyError:
			raise LingoRuntimeError(f'unknown parameter for {owner}: {name!r}') from None

		python_type = JSON_PARAM_TYPES.get(field_type)
		if python_type is None:
			raise LingoRuntimeError(f'param {name!r} has unsupported type for JSON parsing: {field_type!r}')
		if not isinstance(value, python_type) or (python_type is not bool and isinstance(value, bool)):
			raise LingoRuntimeError(f'invalid {field_type} value for param {name!r}: {value!r}')

	return data

def format_key_values(pairs: list[tuple[str, str]], indent: str) -> list[str]:
	"""format 'key: value' lines with the values aligned to the longest key"""

	width = max((len(key) for key, _ in pairs), default=0)
	return [f'{indent}{f"{key}:".ljust(width + 1)} {value}'.rstrip() for key, value in pairs]

def describe_define(ctx: LingoContext, define: L_SYM_define, name_width: int = 0, indent: str = '') -> list[str]:
	"""describe a define (and any nested fields) as indented lines, used by all CLI help output"""

	type_str = define.type
	if define.element_type:
		type_str = f'{type_str}[{define.element_type}]'

	value = f'({type_str})'
	if define.default is not None:
		value += f' default={unwrap_expression(ctx, define.default)!r}'
	if define.secure:
		value += ' secure'
	if define.description:
		value += f' :: {define.description}'

	lines = [f'{indent}{f"{define.name}:".ljust(name_width + 1)} {value}']
	lines.extend(describe_defines(ctx, list((define.fields or {}).values()), indent + '    '))
	return lines

def describe_defines(ctx: LingoContext, defines: list[L_SYM_define], indent: str) -> list[str]:
	"""describe sibling defines with their names padded to the longest name"""

	name_width = max((len(define.name) for define in defines), default=0)
	lines = []
	for define in defines:
		lines.extend(describe_define(ctx, define, name_width, indent))
	return lines

def create_params_help(ctx: LingoContext, params: L_SYM_params | None) -> str:
	lines = ['params:']
	if params is None or not params.fields:
		lines.append('    none')
	else:
		lines.extend(describe_defines(ctx, list(params.fields.values()), '    '))
	return '\n'.join(lines)

def prompt_cli_user_for_param(field_name: str, field_def: L_SYM_define) -> any:
	prompt = f'{field_name} ({field_def.type})'
	if field_def.description:
		prompt += f' - {field_def.description}'
	prompt += ': '

	for _ in range(3):
		raw_value = getpass(prompt) if field_def.secure else input(prompt)
		try:
			return convert_cli_value(field_name, str(field_def.type), raw_value)
		except LingoRuntimeError as e:
			# never echo a secure value back in the error message
			if field_def.secure:
				print(f'Invalid value for secure parameter {field_name!r}; try again.')
			else:
				print(f'Invalid value: {e}')

	raise LingoRuntimeError(f'Max attempts reached for {field_name!r}')

