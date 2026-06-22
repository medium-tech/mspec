from typing import Optional, NamedTuple

from lingolib.types import expression, ValueTypesEnum

#
# spec symbols
#

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

#
# expression symbols
#

class L_SYM_value(NamedTuple):
	"""a value symbol is a symbol that represents a value, such as a variable or a literal"""

	L_SRC: str
	type: ValueTypesEnum
	value: expression
	L_FILE: str = ''
	L_LINE: int = -1

	@property
	def L_SYM_NAME(self):
		return 'value'
	
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

# comparison

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

# int

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


# str

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

# each line corresponds to a function group
ExpressionSymbols = \
	L_SYM_value | L_SYM_error | L_SYM_handle \
	| L_SYM_eq \
	| L_SYM_int | L_SYM_add \
	| L_SYM_str | L_SYM_concat
