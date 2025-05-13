from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

class AddRequest(BaseModel):
    a: float
    b: float

@app.post("/add")
def add_numbers(request: AddRequest):
    result = request.a + request.b
    return {"result": result} 