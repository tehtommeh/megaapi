from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

class SubtractRequest(BaseModel):
    a: float
    b: float

@app.post("/subtract")
def subtract_numbers(request: SubtractRequest):
    result = request.a - request.b
    return {"result": result} 