class LingoLibError(Exception):
	pass

class LingoSyntaxError(LingoLibError):
	pass

class LingoTypeError(LingoLibError):
	pass

class LingoUnknownSymbolError(LingoLibError):
	pass