from shared.api import get_app
from fastapi import File, UploadFile
import hashlib

app = get_app()

@app.post("/hash")
async def hash_file(file: UploadFile = File(...)):
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file.file.read(4096), b""):
        hasher.update(chunk)
    file.file.close()
    return {"sha256": hasher.hexdigest()} 