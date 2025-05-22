from typing import Type
from fastapi import File, UploadFile
from pydantic import BaseModel
import httpx
import random
import os
import io
import tarfile
import asyncio
from shared.api import get_app
from shared.interfaces import SubtractionRequest, SubtractionResponse, AdditionRequest, AdditionResponse, WaitRequest, WaitResponse

app = get_app()

class CalculateRequest(BaseModel):
    x: float

ADDITION_URL = os.getenv("ADDITION_URL", "http://addition:8000/add")
SUBTRACTION_URL = os.getenv("SUBTRACTION_URL", "http://subtraction:8000/subtract")
FILE_SPLITTER_URL = os.getenv("FILE_SPLITTER_URL", "http://file_splitter:8000/split")
FILE_HASHER_URL = os.getenv("FILE_HASHER_URL", "http://file_hasher:8000/hash")
WAIT_URL = os.getenv("WAIT_URL", "http://wait:8000/wait")

async def _call_endpoint(url: str, request: BaseModel, response_type: Type[BaseModel]) -> BaseModel:
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=request.model_dump(), timeout=60)
        resp.raise_for_status()
        return response_type.model_validate(resp.json())

async def call_addition(a: float, b: float) -> float:
    r: AdditionResponse = await _call_endpoint(ADDITION_URL, AdditionRequest(a=a, b=b), AdditionResponse)
    return r.result

async def call_subtraction(a: float, b: float) -> float:
    r: SubtractionResponse = await _call_endpoint(SUBTRACTION_URL, SubtractionRequest(a=a, b=b), SubtractionResponse)
    return r.result

async def call_wait(wait_time: float) -> float:
    r: WaitResponse = await _call_endpoint(WAIT_URL, WaitRequest(wait_time=wait_time), WaitResponse)
    return r

@app.post("/calculate")
async def calculate(request: CalculateRequest):
    x = request.x
    add_rand = random.uniform(1, 10)
    sub_rand = random.uniform(1, 10)
    
    added: float = await call_addition(a=x, b=add_rand)
    subtracted: float = await call_subtraction(a=added, b=sub_rand)
    
    return {
        "initial": x,
        "added_random": add_rand,
        "subtracted_random": sub_rand,
        "result": subtracted
    }

@app.post("/wait")
async def wait(request: WaitRequest):
    wr: WaitResponse = await call_wait(request.wait_time)
    return wr

@app.post("/split-hash")
async def split_and_hash(file: UploadFile = File(...)):
    # Step 1: Call file_splitter to split into 10MB chunks
    ten_mb = 1 * 1024 * 1024
    file.file.seek(0)
    files = {"file": (file.filename, file.file, file.content_type)}
    data = {"size": str(ten_mb)}
    async with httpx.AsyncClient() as client:
        response = await client.post(FILE_SPLITTER_URL, files=files, data=data)
        response.raise_for_status()
        tar_bytes = response.content

    # Step 2: Untar the result
    tar_stream = io.BytesIO(tar_bytes)
    hashes = []
    async def hash_part(part_bytes):
        files = {"file": ("chunk", part_bytes)}
        async with httpx.AsyncClient() as client:
            resp = await client.post(FILE_HASHER_URL, files=files)
            resp.raise_for_status()
            return resp.json()["sha256"]
    with tarfile.open(fileobj=tar_stream, mode="r") as tar:
        tasks = []
        for member in tar.getmembers():
            f = tar.extractfile(member)
            if f:
                part_bytes = f.read()
                tasks.append(hash_part(part_bytes))
        hashes = await asyncio.gather(*tasks)
    return {"result": hashes} 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)