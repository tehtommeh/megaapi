from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from shared.interfaces import SubtractionRequest, SubtractionResponse

app = FastAPI()
Instrumentator().instrument(app).expose(app)

@app.post("/subtract")
def subtract_numbers(request: SubtractionRequest) -> SubtractionResponse:
    result = request.a - request.b
    return SubtractionResponse(result=result) 