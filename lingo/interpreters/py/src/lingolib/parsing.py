from dataclasses import dataclass
import lingolib.symbols as symbols

from lingolib.context import LingoContext
from lingolib.errors import LingoSyntaxError
from lingolib.types import LingoPrimitiveTypeNames, LingoPrimitiveTypes, LingoLiteralTypes


#
# definitions
#


def _get_symbol_by_name(name: str):
	try:
		return getattr(symbols, f'L_SYM_{name}')
	except AttributeError:
		raise LingoSyntaxError(f'no symbol found for name: {name!r}')

@dataclass
class LingoASTExeSpec:
	lingo: symbols.L_SYM_lingo
	main: symbols.L_SYM_main

@dataclass
class LingoASTLibSpec:
	pass

LingoASTSpec = LingoASTExeSpec | LingoASTLibSpec

@dataclass
class LingoASTExpression:
	expression: symbols.ExpressionSymbols


#
# ast creation - specs
#


def create_spec_ast_from_dict(ctx: LingoContext, data: dict) -> LingoASTSpec:

	ctx.log.debug(f'create_spec_ast_from_dict')

	# parse lingo spec block #

	try:
		lingo:symbols.L_SYM_lingo = _get_symbol_by_name('lingo')(**data['lingo'])
	except KeyError:
		raise LingoSyntaxError('missing lingo symbol')
	except Exception as e:
		raise LingoSyntaxError(f'error creating lingo symbol: {e}')
	
	assert isinstance(lingo, symbols.L_SYM_lingo)

	# delegate to spec-specific AST creation #

	if lingo.spec == 'exe':
		return spec_exe_ast_from_dict(ctx, lingo, data)
	else:
		raise LingoSyntaxError(f'unsupported lingo spec: {lingo.spec!r}')


def spec_exe_ast_from_dict(ctx: LingoContext, lingo: symbols.L_SYM_lingo, data: dict) -> LingoASTExeSpec:

	ctx.log.debug(f'spec_exe_ast_from_dict')

	try:
		main_dict = data['main']
	except KeyError:
		raise LingoSyntaxError('missing main symbol')
	
	try:
		main_expr = create_expression_ast(ctx, main_dict)

	except Exception as e:
		raise LingoSyntaxError(f'error creating main expression AST: {e.__class__.__name__}: {e}')
	
	try:
		main:symbols.L_SYM_main = _get_symbol_by_name('main')(expr=main_expr)
	except KeyError:
		raise LingoSyntaxError('missing main symbol')
	except Exception as e:
		raise LingoSyntaxError(f'error creating main symbol: {e}')
	
	assert isinstance(main, symbols.L_SYM_main)

	return LingoASTExeSpec(lingo=lingo, main=main)


#
# ast creation - reusables
#


def create_expression_ast(ctx: LingoContext, data: LingoLiteralTypes) -> symbols.ExpressionSymbols:

	if isinstance(data, LingoPrimitiveTypes):
		ctx.log.debug(f'create_expression_ast - literal: {data!r}')
		return symbols.L_SYM_value(type=type(data).__name__, value=data)

	elif isinstance(data, list):
		ctx.log.debug(f'create_expression_ast - list: {data!r}')
		return [create_expression_ast(ctx, item) for item in data]
	
	elif isinstance(data, dict):
		return create_expression_ast_from_dict(ctx, data)
	
	else:
		raise LingoSyntaxError(f'unsupported expression type: {type(data).__name__!r}')
	

def create_expression_ast_from_dict(ctx: LingoContext, data: dict) -> symbols.ExpressionSymbols:

	keys = set(data.keys())
	ctx.log.debug(f'create_expression_ast_from_dict - keys: {keys!r}')
	
	if keys == {'str'}:
		return symbols.L_SYM_str(object=create_expression_ast(ctx, data['str']))
		
	elif keys == {'type', 'value'}:

		if data['type'] not in LingoPrimitiveTypeNames:
			raise LingoSyntaxError(f'invalid type for value symbol: {data["type"]!r}')
		
		elif isinstance(data['value'], LingoPrimitiveTypes) and type(data['value']).__name__ != data['type']:
			raise LingoSyntaxError(f'value type mismatch: expected {data["type"]!r}, got {type(data["value"]).__name__!r}')
		
		else:
			if isinstance(data['value'], LingoPrimitiveTypes):
				return symbols.L_SYM_value(type=data['type'], value=data['value'])
			else:
				return symbols.L_SYM_value(type=data['type'], value=create_expression_ast(ctx, data['value']))

	elif keys == {'concat'}:
		if isinstance(data['concat'], list):
			ctx.log.debug(f'create_expression_ast_from_dict - concat expression: {data["concat"]!r}')
			return symbols.L_SYM_concat(items=create_expression_ast(ctx, data['concat']))
		else:
			raise LingoSyntaxError(f'concat symbol must have a list')
	
	else:
		raise LingoSyntaxError(f'unsupported expression dict: {data!r}')
	

#
# misc
#


def lingo_ast_to_string(spec: LingoASTSpec, indent=0):
	"""
	recursively print a lingo AST spec in a human-readable format

	iterate over all attr pairs
		if the attr name starts w/ _ - skip (internal attr)
		if the attr value name starts with 'L_SYM' print it with indent
	"""
	attr_names = filter(lambda name: not name.startswith('_') and not name.startswith('L_SYM'), dir(spec))
	output = []
	for name in attr_names:
		value = getattr(spec, name)
		if hasattr(value, 'L_SYM_NAME'):
			output.append('  ' * indent + f'L_SYM_{value.L_SYM_NAME}')
			output.append(lingo_ast_to_string(value, indent + 1))

		elif isinstance(value, list):
			output.append('  ' * indent + f'{name}:')
			for item in value:
				if hasattr(item, 'L_SYM_NAME'):
					output.append('  ' * (indent + 1) + f'L_SYM_{item.L_SYM_NAME}')
					output.append(lingo_ast_to_string(item, indent + 2))
				else:
					output.append('  ' * (indent + 1) + f'{item!r}')
		elif isinstance(value, (str, int, float, bool)):
			output.append('  ' * indent + f'{name}: {value!r}')

	return '\n'.join(output)