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
PythonTypeNamesToLingoTypes = {
	'bool': 'bool',
	'int': 'int',
	'str': 'str',
	'float': 'float',
	'list': 'list',
	'dict': 'struct'
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

class LingoStyleColors(StrEnum):

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

class LingoStyleOptions(NamedTuple):
	bold: bool = False
	italic: bool = False
	underline: bool = False
	color: str = 'black'

	def validate(self) -> 'LingoStyleOptions':
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

		return self

class LingoListDisplayFormats(StrEnum):
	numbers = 'numbers'
	bullets = 'bullets'
	table = 'table'

class LingoTableHeader(NamedTuple):
	text: str
	field: str

class LingoListDisplayOptions(NamedTuple):
	format: LingoListDisplayFormats = LingoListDisplayFormats.bullets
	headers: list[LingoTableHeader] = []
	columns: list[str] = []

	def validate(self) -> 'LingoListDisplayOptions':
		if not isinstance(self.format, LingoListDisplayFormats):
			raise ValueError(f'Invalid value for format: {self.format}')
		
		if not isinstance(self.headers, list):
			raise ValueError(f'Invalid value for headers: {self.headers}')
		
		for n, header in enumerate(self.headers):
			if not isinstance(header, LingoTableHeader):
				raise ValueError(f'Invalid header at index {n}: {str(header)[0:50]}')
			
		if not isinstance(self.columns, list):
			raise ValueError(f'Invalid value for columns: {self.columns}')
		
		for column in self.columns:
			if not isinstance(column, str):
				raise ValueError(f'Invalid column: {column}')

		if self.format == LingoListDisplayFormats.table:
			len_headers = len(self.headers)
			len_columns = len(self.columns)
			if len_headers > 0 and len_columns > 0:
				raise ValueError(f'Cannot specify both headers and columns for table display format.')
			if len_headers == 0 and len_columns == 0:
				raise ValueError(f'Must specify either headers or columns for table display format.')

		return self

	@classmethod
	def from_dict(cls, data: dict) -> 'LingoListDisplayOptions':

		for key in data.keys():
			if key not in {'format', 'headers', 'columns'}:
				raise ValueError(f'unsupported key in lingo list display options: {key!r}')

		parsed_data = {}
		
		format_raw = data.get('format', LingoListDisplayFormats.bullets)
		if isinstance(format_raw, str):
			parsed_data['format'] = LingoListDisplayFormats(format_raw)
		else:
			parsed_data['format'] = format_raw

		parsed_data['headers'] = [LingoTableHeader(**header) for header in data.get('headers', [])]
		parsed_data['columns'] = data.get('columns', [])

		return cls(**parsed_data).validate()
