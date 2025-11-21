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