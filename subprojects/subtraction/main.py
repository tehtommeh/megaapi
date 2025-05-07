from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class SubtractRequest(BaseModel):
    a: float
    b: float

@app.post("/subtract")
def subtract_numbers(request: SubtractRequest):
    result = request.a - request.b
    return {"result": result} 