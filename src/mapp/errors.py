import json


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
            
class ResponseError(MappError):
    def __init__(self, message: str):
        super().__init__('RESPONSE_ERROR', message)

    @classmethod
    def from_json(cls, json_data: str) -> 'ResponseError':
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON data.')

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'ResponseError':
        try:
            code = data['error']['code']
            message = data['error']['message']
        except KeyError:
            raise ValueError('Invalid error data format.')

        match code:
            case 'NOT_FOUND':
                return NotFoundError(message)
            case 'AUTHENTICATION_ERROR':
                return AuthenticationError(message)
            case 'FORBIDDEN_ERROR':
                return ForbiddenError(message)
            case _:
                return ResponseError(message)

class ServerError(MappError):
    def __init__(self, message: str):
        super().__init__('SERVER_ERROR', message)

class NotFoundError(MappError):
    def __init__(self, message: str):
        super().__init__('NOT_FOUND', message)

class AuthenticationError(MappError):
    def __init__(self, message: str):
        super().__init__('AUTHENTICATION_ERROR', message)

class ForbiddenError(MappError):
    def __init__(self, message: str):
        super().__init__('FORBIDDEN_ERROR', message)
