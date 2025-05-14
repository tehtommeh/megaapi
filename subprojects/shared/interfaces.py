from pydantic import BaseModel

class SubtractionRequest(BaseModel):
    a: int
    b: int

class SubtractionResponse(BaseModel):
    result: int
    