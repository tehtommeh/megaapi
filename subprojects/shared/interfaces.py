from pydantic import BaseModel

class SubtractionRequest(BaseModel):
    a: float
    b: float

class SubtractionResponse(BaseModel):
    result: float

class AdditionRequest(BaseModel):
    a: float
    b: float

class AdditionResponse(BaseModel):
    result: float

class WaitRequest(BaseModel):
    wait_time: float

class WaitResponse(BaseModel):
    waited: bool
    start_time: str
    end_time: str