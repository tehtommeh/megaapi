from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import httpx
import random
import os
import io
import tarfile
import asyncio
from prometheus_fastapi_instrumentator import Instrumentator
from shared.interfaces import SubtractionResponse

app = FastAPI()
Instrumentator().instrument(app).expose(app)

class CalculateRequest(BaseModel):
    x: float

ADDITION_URL = os.getenv("ADDITION_URL", "http://addition:8000/add")
SUBTRACTION_URL = os.getenv("SUBTRACTION_URL", "http://subtraction:8000/subtract")
FILE_SPLITTER_URL = os.getenv("FILE_SPLITTER_URL", "http://file_splitter:8000/split")
FILE_HASHER_URL = os.getenv("FILE_HASHER_URL", "http://file_hasher:8000/hash")

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
        b = SubtractionResponse(a=added, b=sub_rand)
        sub_resp = client.post(SUBTRACTION_URL, json=b)
        sub_resp.raise_for_status()
        result = sub_resp.json()["result"]
    
    return {
        "initial": x,
        "added_random": add_rand,
        "subtracted_random": sub_rand,
        "result": result
    }

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