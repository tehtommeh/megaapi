from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import random
import os

app = FastAPI()

class CalculateRequest(BaseModel):
    x: float

ADDITION_URL = os.getenv("ADDITION_URL", "http://addition:8000/add")
SUBTRACTION_URL = os.getenv("SUBTRACTION_URL", "http://subtraction:8000/subtract")

@app.post("/calculate")
def calculate(request: CalculateRequest):
    x = request.x
    add_rand = random.uniform(1, 10)
    sub_rand = random.uniform(1, 10)
    
    # Call addition service
    with httpx.Client() as client:
        add_resp = client.post(ADDITION_URL, json={"a": x, "b": add_rand})
        add_resp.raise_for_status()
        added = add_resp.json()["result"]
    
    # Call subtraction service
    with httpx.Client() as client:
        sub_resp = client.post(SUBTRACTION_URL, json={"a": added, "b": sub_rand})
        sub_resp.raise_for_status()
        result = sub_resp.json()["result"]
    
    return {
        "initial": x,
        "added_random": add_rand,
        "subtracted_random": sub_rand,
        "result": result
    } 