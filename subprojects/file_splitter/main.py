from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import io
import tarfile
from shared.api import get_app

app = get_app()

@app.post("/split")
async def split_file(file: UploadFile = File(...), size: int = Form(...)):
    # Read the file into memory
    file_bytes = file.file.read()
    parts = [file_bytes[i:i+size] for i in range(0, len(file_bytes), size)]

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        for idx, part in enumerate(parts):
            info = tarfile.TarInfo(name=f"part_{idx+1}")
            info.size = len(part)
            tar.addfile(tarinfo=info, fileobj=io.BytesIO(part))
    tar_stream.seek(0)
    return StreamingResponse(tar_stream, media_type="application/x-tar", headers={"Content-Disposition": "attachment; filename=split_parts.tar"}) 