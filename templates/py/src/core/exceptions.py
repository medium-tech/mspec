class NotFoundError(Exception):
    pass

class RequestError(Exception):
    def __init__(self, status:str, msg:str) -> None:
        super().__init__(msg)
        self.status = status
        self.msg = msg

class JSONResponse(Exception):
    def __init__(self, status:str, data:dict|None=None) -> None:
        super().__init__('JSONResponse')
        self.status = status
        self.data = data
