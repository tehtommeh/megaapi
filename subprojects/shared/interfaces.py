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