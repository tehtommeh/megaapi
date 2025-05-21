from functools import lru_cache
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse
import nemo.collections.asr as nemo_asr
import tempfile
import shutil
import os
from shared.api import get_app

app = get_app()

# Load the model once at startup
@lru_cache
def load_model():
    model = nemo_asr.models.ASRModel.from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v2")
    # Handle long audio
    # https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2/discussions/15
    # https://developer.nvidia.com/blog/pushing-the-boundaries-of-speech-recognition-with-nemo-parakeet-asr-models/#parakeet_models_for_long-form_speech_inference
    model.change_attention_model("rel_pos_local_attn", [128, 128])  # local attn
    model.change_subsampling_conv_chunking_factor(1)  # 1 = auto select
    return model

asr_model = load_model()

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Save uploaded file to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        output = asr_model.transcribe([tmp_path], timestamps=True)
        text = output[0].text
    finally:
        os.remove(tmp_path)
    return JSONResponse({"text": text})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)