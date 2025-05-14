from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from shared.interfaces import AdditionRequest, AdditionResponse

app = FastAPI()
Instrumentator().instrument(app).expose(app)


@app.post("/add")
def add_numbers(request: AdditionRequest) -> AdditionResponse:
    result = request.a + request.b
    return AdditionResponse(result=result) 