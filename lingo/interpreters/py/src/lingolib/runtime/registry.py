"""

allow access to:
- ops parsed from local gui spec
(future features)
- functions loaded from lib spec
- data loaded from data spec
- backed specs from app spec

"""

import os

from lingolib.symbols import L_SYM_ops, L_SYM_modules, L_SYM_imports, L_SYM_func, L_SYM_value, L_SYM_define
from lingolib.context import (
	LingoRegisteredFunction,
	LingoRegisteredValue,
	LingoRegisteredDefinition,
	LingoRegistry,
	LingoContext,
)
from lingolib.errors import LingoRuntimeError
from lingolib.parsing import create_spec_ast_from_dict, YamlLocationLoader, LingoASTLibSpec
import yaml

__all__ = [
	'init_registry',
	'add_ops_to_registry',
	'add_modules_to_registry',
	'add_lib_to_registry',
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
