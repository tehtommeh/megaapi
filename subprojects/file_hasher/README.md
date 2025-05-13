# Filehasher FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/hash` to compute the SHA256 hash of an uploaded file.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Usage

Send a POST request to `http://localhost:8000/hash` with a file upload (form field name: `file`).

Example using `curl`:
```bash
curl -F "file=@path/to/your/file" http://localhost:8000/hash
```

Response:
```
{
  "sha256": "...hash..."
}
``` 