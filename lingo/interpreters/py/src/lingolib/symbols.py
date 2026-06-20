from typing import Optional, NamedTuple

from lingolib.types import expression, ValueTypesEnum

#
# spec symbols
#

class L_SYM_lingo(NamedTuple):

	spec: str
	version: str

	def __str__(self):
		return f'L_SYM_lingo(spec={self.spec!r}, version={self.version!r})'

	@property
	def L_SYM_NAME(self):
		return 'lingo'
	
	@property
	def L_SYM_TYPE(self):
		return 'spec'


class L_SYM_main(NamedTuple):
	expr: expression

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

	type: ValueTypesEnum
	value: expression

	@property
	def L_SYM_NAME(self):
		return 'value'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_str(NamedTuple):
	"""symbolt for the str function"""
	object: str|expression

	@property
	def L_SYM_NAME(self):
		return 'str'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

class L_SYM_concat(NamedTuple):
	"""symbol for the concat function"""
	items: list[str|expression]

	@property
	def L_SYM_NAME(self):
		return 'concat'
	
	@property
	def L_SYM_TYPE(self):
		return 'expression'

ExpressionSymbols = L_SYM_value | L_SYM_str | L_SYM_concat

