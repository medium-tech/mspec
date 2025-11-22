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
