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

from collections import namedtuple

from lingolib.symbols import L_SYM_ops, L_SYM_lib_modules, L_SYM_imports, L_SYM_func, L_SYM_value, L_SYM_define, L_SYM_params
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
from lingolib.runtime.shared import parse_cli_params, convert_cli_value, CLIHelpMenuRequested, create_help_string, prompt_cli_user_for_param

import yaml

__all__ = [
	'init_registry',
	'add_ops_to_registry',
	'add_modules_to_registry',
	'add_lib_to_registry',
	'add_params_to_registry',
]


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

def add_modules_to_registry(ctx: LingoContext, modules: L_SYM_lib_modules):
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

def resolve_model_define(ctx: LingoContext, model: L_SYM_define) -> L_SYM_define:
	"""return the define for an app model, following a 'model' reference into the imported libs"""
	if model.reference is None:
		return model

	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')

	try:
		registered = ctx.registry.lib[model.reference]
	except KeyError:
		raise LingoRuntimeError(f'model reference {model.reference!r} not found in imported libraries') from None

	if not isinstance(registered, LingoRegisteredDefinition):
		raise LingoRuntimeError(f'model reference {model.reference!r} must resolve to a define, got: {type(registered).__name__}')

	return registered.ast


#
# params | cli input parsing
#

def add_params_to_registry(ctx: LingoContext, params: L_SYM_params, cli_args: list[str] = []):
	
	if ctx.registry is None:
		raise RuntimeError('LingoContext.registry has not been initialized')

	try:
		raw_cli_values, interactive_enabled = parse_cli_params(cli_args)
	except CLIHelpMenuRequested:
		print(create_help_string(ctx, params))
		sys.exit(0)

	sep = lambda msg: print(f'\n{"=" * 15} {msg} {"=" * 15}')

	user_was_prompted = False
	raw_values = {}

	for field_name, field_def in params.fields.items():
		try:
			raw_value = raw_cli_values[field_name]
			raw_values[field_name] = convert_cli_value(field_name, field_def.type, raw_value)

		except KeyError:
			if field_def.default is not None:
				raw_values[field_name] = unwrap_expression(ctx, field_def.default)
			elif interactive_enabled:
				if not user_was_prompted:
					sep('start interactive mode')
				raw_values[field_name] = prompt_cli_user_for_param(field_name, field_def)
				user_was_prompted = True
			else:
				raise LingoRuntimeError(f'missing required param: {field_name!r}')

	if user_was_prompted:
		sep('end interactive mode')

	ctx.registry.params = namedtuple('Params', raw_values.keys())(**raw_values)
	