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
	ui = 'ui'

LingoScriptSpecs = [spec.value for spec in LingoScriptSpecsEnum]


class LingoValue(NamedTuple):
	type: ValueTypesEnum
	value: LingoLiteralTypes

class LingoLanguageError(NamedTuple):
	error: str
	code: str = 'ERROR'