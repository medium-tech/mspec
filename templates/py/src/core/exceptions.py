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

class JSONResponse(MSpecError):
    def __init__(self, status:str, data:dict|None=None) -> None:
        super().__init__('JSONResponse')
        self.status = status
        self.data = data
