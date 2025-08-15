class MSpecError(Exception):
    pass

class ConfigError(MSpecError):
    pass

class NotFoundError(MSpecError):
    pass

class AuthenticationError(MSpecError):
    pass

class ForbiddenError(MSpecError):
    pass

class RequestError(MSpecError):
    def __init__(self, status:str, msg:str) -> None:
        super().__init__(msg)
        self.status = status
        self.msg = msg

class PlainTextResponse(MSpecError):
    content_type = 'text/plain'
    def __init__(self, status:str, text:str) -> None:
        super().__init__('PlainTextResponse')
        self.status = status
        self.text = text

class JSONResponse(MSpecError):
    content_type = 'application/json'
    def __init__(self, status:str, data:dict|None=None) -> None:
        super().__init__('JSONResponse')
        self.status = status
        self.data = data