from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class AddRequest(BaseModel):
    a: float
    b: float

@app.post("/add")
def add_numbers(request: AddRequest):
    result = request.a + request.b
    return {"result": result} 