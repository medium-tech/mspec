from typing import Optional, NamedTuple

from lingolib.types import LingoListDisplayOptions, expression, ValueTypesEnum, LingoStyleOptions


#####
#
#
# expression symbols
#
#
#####

#
# core
#

class L_SYM_call(NamedTuple):
	"""call a lib module function by dotted reference, with args keyed by parameter name"""

	L_SRC: str
	func: str
	args: dict[str, expression]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'call'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_value(NamedTuple):
	"""a value symbol is a symbol that represents a value, such as a variable or a literal"""

	L_SRC: str
	type: ValueTypesEnum
	value: expression
	element_type: str = ''
	display: LingoListDisplayOptions|None = None
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'value'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_define(NamedTuple):

	L_SRC: str
	name: str
	type: ValueTypesEnum | None
	default: expression|None = None
	element_type: str = ''
	display: LingoListDisplayOptions|None = None
	description: str = ''
	secure: bool = False
	fields: 'dict[str, L_SYM_define] | None' = None
	L_FILE: str = ''
	L_LINE: int = -1
	reference: str | None = None

	@property
	def L_SYM_NAME(self):
		return 'define'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'
	
class L_SYM_error(NamedTuple):

	L_SRC: str
	error: str|expression
	code: Optional[str|expression] = 'ERROR'
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'error'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'
	
class L_SYM_handle(NamedTuple):
	"""convert an error to a str and return it, otherwise return the value of the expression"""
	
	L_SRC: str
	expr: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'handle'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_get(NamedTuple):
	"""access a named field from a data source, e.g. get: state.counter (shorthand) or get: {field: counter, from: state}"""

	L_SRC: str
	field: str
	from_: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'get'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_validate(NamedTuple):
	"""validate an expression's value against a define shape, either inline or a dotted reference to an imported module define"""

	L_SRC: str
	item: expression
	against: L_SYM_define | str
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'validate'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_create(NamedTuple):
	"""insert a row for an app model and return the stored object, including its generated id; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	data: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_create'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_read(NamedTuple):
	"""return the stored object with the given id; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	id: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_read'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_list(NamedTuple):
	"""return a page of stored objects as a struct with items and total; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	offset: expression | None = None
	limit: expression | None = None
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_list'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_put(NamedTuple):
	"""replace all fields of the stored object with the given id; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	id: expression
	data: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_put'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_patch(NamedTuple):
	"""update a subset of fields of the stored object with the given id; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	id: expression
	data: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_patch'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_db_delete(NamedTuple):
	"""delete the stored object with the given id and return it; only evaluated by the server runtime"""

	L_SRC: str
	model: str
	id: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'db_delete'

	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_args(NamedTuple):
	"""reference to a named argument of the enclosing func"""

	L_SRC: str
	name: str
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'args'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_set(NamedTuple):

	L_SRC: str
	name: str
	value: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'set'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_func(NamedTuple):

	L_SRC: str
	name: str
	args: list[expression] | None = None
	func: expression | None = None
	return_: L_SYM_define | None = None
	description: str = ''
	L_FILE: str = ''
	L_LINE: int = -1
	reference: str | None = None

	@property
	def L_SYM_NAME(self):
		return 'func'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

#
# comparison
#

class L_SYM_eq(NamedTuple):

	L_SRC: str
	a: expression
	b: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'eq'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

#
# int
#

class L_SYM_int(NamedTuple):

	L_SRC: str
	number: int|str|expression
	base: int|expression = 10
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'int'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'
	
class L_SYM_add(NamedTuple):

	L_SRC: str
	a: int|expression
	b: int|expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'add'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

#
# str
#

class L_SYM_str(NamedTuple):
	"""symbolt for the str function"""

	L_SRC: str
	object: str|expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'str'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_concat(NamedTuple):
	"""symbol for the concat function"""

	L_SRC: str
	items: list[str|expression]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'concat'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'
	
class L_SYM_join(NamedTuple):
	"""symbol for the join function"""

	L_SRC: str
	items: list[str|expression]
	separator: str|expression = ', '
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'join'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'


#
# display
#


class L_SYM_block(NamedTuple):

	L_SRC: str
	items: list[expression]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'block'

	@property
	def L_SYM_TYPE(self):
		return 'display'


class L_SYM_text(NamedTuple):

	L_SRC: str
	text: expression
	style: LingoStyleOptions
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'text'

	@property
	def L_SYM_TYPE(self):
		return 'display'


class L_SYM_break(NamedTuple):

	L_SRC: str
	breaks: expression | None = None
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'break'

	@property
	def L_SYM_TYPE(self):
		return 'display'


class L_SYM_link(NamedTuple):

	L_SRC: str
	link: expression | str = ''
	text: expression | str = ''
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'link'

	@property
	def L_SYM_TYPE(self):
		return 'display'


class L_SYM_heading(NamedTuple):

	L_SRC: str
	text: expression | None = None
	level: int = 1
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'heading'

	@property
	def L_SYM_TYPE(self):
		return 'display'

class L_SYM_button(NamedTuple):

	L_SRC: str
	call: str = ''
	text: expression | str = ''
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'button'

	@property
	def L_SYM_TYPE(self):
		return 'display'

# each line corresponds to a function group

ExpressionSymbols = \
	L_SYM_value | L_SYM_define | L_SYM_error | L_SYM_handle | L_SYM_get | L_SYM_set | L_SYM_func \
	| L_SYM_args \
	| L_SYM_call | L_SYM_validate \
	| L_SYM_db_create | L_SYM_db_read | L_SYM_db_list | L_SYM_db_put | L_SYM_db_patch | L_SYM_db_delete \
	| L_SYM_eq \
	| L_SYM_int | L_SYM_add \
	| L_SYM_str | L_SYM_concat | L_SYM_join \
	| L_SYM_text | L_SYM_break | L_SYM_link | L_SYM_heading | L_SYM_button


#####
#
#
# spec symbols
#
#
#####

class L_SYM_lingo(NamedTuple):

	L_SRC: str
	spec: str
	version: str
	L_FILE: str = ''
	L_LINE: int = -1

	
	def __str__(self):
		return f'L_SYM_lingo(spec={self.spec!r}, version={self.version!r})'

	@property
	def L_SYM_NAME(self):
		return 'lingo'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'


class L_SYM_main(NamedTuple):

	L_SRC: str
	expr: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'main'

	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_imports(NamedTuple):
	"""paths of lib specs to import, e.g. for use with the call and validate symbols"""

	L_SRC: str
	paths: list[str]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'imports'

	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_state(NamedTuple):

	L_SRC: str
	fields: dict[str, L_SYM_define]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'state'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_params(NamedTuple):
	"""user-supplied input for an exe spec (cli args) or gui spec (url query string args)"""

	L_SRC: str
	fields: dict[str, L_SYM_define]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'params'

	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_ops(NamedTuple):
	
	L_SRC: str
	funcs: dict[str, L_SYM_func]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'ops'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_lib_module(NamedTuple):

	L_SRC: str
	name: str
	members: dict[str, L_SYM_define | L_SYM_value | L_SYM_func]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'module'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_lib_modules(NamedTuple):

	L_SRC: str
	members: dict[str, L_SYM_lib_module]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'modules'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_app_module(NamedTuple):

	L_SRC: str
	name: str
	ops: L_SYM_ops
	models: dict[str, L_SYM_define]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'app_module'

	@property
	def L_SYM_TYPE(self):
		return 'spec'

class L_SYM_app_modules(NamedTuple):

	L_SRC: str
	members: dict[str, L_SYM_app_module]
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'app_modules'

	@property
	def L_SYM_TYPE(self):
		return 'spec'
