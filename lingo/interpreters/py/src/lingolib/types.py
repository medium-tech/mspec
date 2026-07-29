from enum import StrEnum
from typing import NamedTuple


class expression:
	pass

class ValueTypesEnum(StrEnum):
	bool = 'bool'
	int = 'int'
	str = 'str'
	float = 'float'

LingoPrimitiveTypes = bool | int | str | float
LingoLiteralTypes = LingoPrimitiveTypes | list | dict

LingoPrimitiveTypeNames = {'bool', 'int', 'str', 'float'}
LingoLiteralTypeNames = LingoPrimitiveTypeNames | {'list', 'struct'}
LingoTypesToPythonTypes = {
	'bool': bool,
	'int': int,
	'str': str,
	'float': float,
	'list': list,
	'struct': dict
}
LingoTypesToPythonTypeNames = {
	'bool': 'bool',
	'int': 'int',
	'str': 'str',
	'float': 'float',
	'list': 'list',
	'struct': 'dict'
}

class LingoScriptSpecsEnum(StrEnum):
	app = 'app'
	exe = 'exe'
	lib = 'lib'
	text = 'text'
	ui = 'ui'

LingoScriptSpecs = [spec.value for spec in LingoScriptSpecsEnum]


class LingoValue(NamedTuple):
	type: ValueTypesEnum
	value: LingoLiteralTypes

class LingoLanguageError(NamedTuple):
	error: str
	code: str = 'ERROR'

def value_to_str(value:LingoLiteralTypes) -> str:
	if isinstance(value, bool):
		return 'true' if value else 'false'
	else:
		return str(value)

def error_to_str(error:LingoLanguageError) -> str:
	return f'LINGO_ERROR [{error.code}] - {error.error}'

def LingoStyleColors(StrEnum):

	# shades of gray
	white = 'white'
	light_gray = 'lightgray'
	gray = 'gray'
	dark_gray = 'darkgray'
	black = 'black'

	# roygbiv
	red = 'red'
	orange = 'orange'
	yellow = 'yellow'
	green = 'green'
	blue = 'blue'
	indigo = 'indigo'
	violet = 'violet'

	# cmyk
	cyan = 'cyan'
	magenta = 'magenta'
	# yellow = 'yellow' - defined above
	# black = 'black' - defined above

LingoStyleColorsList = [color.value for color in LingoStyleColors]

def LingoStyleBlock(NamedTuple):
	bold: bool = False
	italic: bool = False
	underline: bool = False
	color: str = 'black'

	def validate(self):
		if not isinstance(self.bold, bool):
			raise ValueError(f'Invalid value for bold: {self.bold}')
		if not isinstance(self.italic, bool):
			raise ValueError(f'Invalid value for italic: {self.italic}')
		if not isinstance(self.underline, bool):
			raise ValueError(f'Invalid value for underline: {self.underline}')
		if not isinstance(self.color, str):
			raise ValueError(f'Invalid value for color: {self.color}')
		if self.color not in LingoStyleColorsList:
			raise ValueError(f'Invalid color: {self.color}')