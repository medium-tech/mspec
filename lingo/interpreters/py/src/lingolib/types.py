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
LingoLiteralTypeNames = LingoPrimitiveTypeNames | {'list', 'dict'}

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