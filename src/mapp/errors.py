class MappError(Exception):
    
    def __init__(self, code:str, message: str):
        super().__init__(f'[MappError {code}] {message}')
        self.code = code
        self.error_message = message

    def to_dict(self) -> dict:
        return {
            'error': {
                'code': self.code,
                'message': self.error_message
            }
        }

    
class MappValidationError(MappError):
    def __init__(self, message: str, field_errors:dict):
        super().__init__('VALIDATION_ERROR', message)
        self.field_errors = field_errors

    def to_dict(self) -> dict:
        error_dict = super().to_dict()
        error_dict['error']['field_errors'] = self.field_errors
        return error_dict


class RequestError(MappError):
    def __init__(self, message: str):
        super().__init__('REQUEST_ERROR', message)

    @classmethod
    def from_code(cls, code:int, exc:Exception) -> 'RequestError':
        match code:
            case 401:
                return AuthenticationError(str(exc))
            case 403:
                return ForbiddenError(str(exc))
            case 404:
                return NotFoundError(str(exc))
            case _:
                return RequestError(str(exc))


class ServerError(MappError):
    def __init__(self, message: str):
        super().__init__('SERVER_ERROR', message)


class NotFoundError(RequestError):
    def __init__(self, message: str):
        super().__init__('NOT_FOUND', message)


class AuthenticationError(RequestError):
    def __init__(self, message: str):
        super().__init__('AUTHENTICATION_ERROR', message)


class ForbiddenError(RequestError):
    def __init__(self, message: str):
        super().__init__('FORBIDDEN_ERROR', message)
