"""

allow access to:
- ops parsed from local gui spec
(future features)
- functions loaded from lib spec
- data loaded from data spec
- backed specs from app spec

"""

import os
import sys

from getpass import getpass

from lingolib.symbols import L_SYM_ops, L_SYM_modules, L_SYM_imports, L_SYM_func, L_SYM_value, L_SYM_define, L_SYM_params
from lingolib.context import (
	LingoRegisteredFunction,
	LingoRegisteredValue,
	LingoRegisteredDefinition,
	LingoRegistry,
	LingoContext,
)
from lingolib.errors import LingoRuntimeError
from lingolib.parsing import create_spec_ast_from_dict, YamlLocationLoader, LingoASTLibSpec
from lingolib.runtime.eval_expression import unwrap_expression

import yaml

__all__ = [
	'init_registry',
	'add_ops_to_registry',
	'add_modules_to_registry',
	'add_lib_to_registry',
	'add_params_to_registry',
]

class CLIHelpMenuRequested(Exception):
	pass

#
# api
#

def init_registry(ctx: LingoContext, ops: L_SYM_ops | None = None):
	if ctx.registry is None:
		ctx.registry = LingoRegistry()
	else:
		raise RuntimeError('Runtime registry has already been initialized')
	
	if ops is not None:
		add_ops_to_registry(ctx, ops)

def add_ops_to_registry(ctx: LingoContext, ops: L_SYM_ops):
	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')

	for op_name, op_func in ops.funcs.items():
		ctx.registry.ops[op_name] = LingoRegisteredFunction(name=op_name, ast=op_func)

def add_modules_to_registry(ctx: LingoContext, modules: L_SYM_modules):
	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')
	
	for module_name, module in modules.members.items():
		for member_name, member in module.members.items():
			key = f'{module_name}.{member_name}'
			if isinstance(member, L_SYM_func):
				ctx.registry.lib[key] = LingoRegisteredFunction(name=key, ast=member)
			elif isinstance(member, L_SYM_value):
				ctx.registry.lib[key] = LingoRegisteredValue(name=key, ast=member)
			elif isinstance(member, L_SYM_define):
				ctx.registry.lib[key] = LingoRegisteredDefinition(name=key, ast=member)
			else:
				raise RuntimeError(f'unsupported module member type for {key!r}: {type(member).__name__}')

def add_lib_to_registry(ctx: LingoContext, imports: L_SYM_imports):
	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')

	base_dir = os.path.dirname(imports.L_FILE) if imports.L_FILE else ''

	for import_path in imports.paths:
		# import paths are relative to the file that declared the imports symbol
		resolved_path = os.path.join(base_dir, import_path) if base_dir else import_path

		try:
			with open(resolved_path) as f:
				doc = yaml.load(f.read(), Loader=YamlLocationLoader)
		except FileNotFoundError:
			raise LingoRuntimeError(f'import {import_path!r} not found (resolved path: {resolved_path!r})') from None
		except yaml.YAMLError as e:
			raise LingoRuntimeError(f'failed to parse import {import_path!r} (resolved path: {resolved_path!r}): {e}') from None
		except Exception as e:
			raise LingoRuntimeError(f'failed to import {import_path!r} (resolved path: {resolved_path!r}): {e}') from None

		parser_ctx = LingoContext.add_parser_context(ctx, src='', file=os.path.abspath(resolved_path), line=0, col=0)
		import_ast = create_spec_ast_from_dict(parser_ctx, doc)

		if not isinstance(import_ast, LingoASTLibSpec):
			raise LingoRuntimeError(f'import {import_path!r} must be a lib spec, got: {type(import_ast).__name__}')

		add_modules_to_registry(ctx, import_ast.modules)

CLI_BOOL_TRUE_VALUES = {'1', 't', 'true', 'y', 'yes'}
CLI_BOOL_FALSE_VALUES = {'0', 'f', 'false', 'n', 'no'}

#
# params | cli input parsing
#

def _parse_cli_bool(field_name: str, raw_value: str) -> bool:
	normalized = raw_value.lower()
	if normalized in CLI_BOOL_TRUE_VALUES:
		return True
	elif normalized in CLI_BOOL_FALSE_VALUES:
		return False
	else:
		raise LingoRuntimeError(f'invalid bool value for param {field_name!r}: {raw_value!r}')

def _convert_cli_value(field_name: str, field_type: str, raw_value: str):
	match field_type:
		case 'bool':
			return _parse_cli_bool(field_name, raw_value)
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

def _parse_cli_params(fields: dict[str, L_SYM_define], cli_args: list[str]) -> tuple[dict[str, str], bool]:
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

def _create_help_string(ctx: LingoContext, params: L_SYM_params) -> str:
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

def _prompt_cli_user_for_param(field_name: str, field_def: L_SYM_define) -> any:
	while True:
		print(f'Field {field_name} ({field_def.type})')
		print(f'\tDescription: {field_def.description}')

		if field_def.secure:
			raw_value = getpass(f'Enter value (secure): ')
		else:
			raw_value = input(f'Enter value: ')

		try:
			return _convert_cli_value(field_name, field_def.type, raw_value)
		except LingoRuntimeError as e:
			print(f'Invalid value: {e.__class__.__name__}: {e}')


def add_params_to_registry(ctx: LingoContext, params: L_SYM_params, cli_args: list[str] = []):
	
	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')

	try:
		raw_cli_values, interactive_enabled = _parse_cli_params(params.fields, cli_args)
	except CLIHelpMenuRequested:
		print(_create_help_string(ctx, params))
		sys.exit(0)

	sep = lambda msg: print(f'\n{"=" * 15} {msg} {"=" * 15}')

	user_was_prompted = False

	for field_name, field_def in params.fields.items():
		try:
			raw_value = raw_cli_values[field_name]
			ctx.registry.params[field_name] = _convert_cli_value(field_name, field_def.type, raw_value)

		except KeyError:
			if field_def.default is not None:
				ctx.registry.params[field_name] = unwrap_expression(ctx, field_def.default)
			elif interactive_enabled:
				if not user_was_prompted:
					sep('start interactive mode')
				ctx.registry.params[field_name] = _prompt_cli_user_for_param(field_name, field_def)
				user_was_prompted = True
			else:
				raise LingoRuntimeError(f'missing required param: {field_name!r}')

	if user_was_prompted:
		sep('end interactive mode')
