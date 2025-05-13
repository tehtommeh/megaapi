from fastapi import FastAPI, File, UploadFile
import hashlib

app = FastAPI()

@app.post("/hash")
def hash_file(file: UploadFile = File(...)):
    hasher = hashlib.sha256()
    for chunk in iter(lambda: file.file.read(4096), b""):
        hasher.update(chunk)
    file.file.close()
    return {"sha256": hasher.hexdigest()} 