# File Splitter FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/split` to split an uploaded file into parts of a specified size (in bytes) and returns a tar archive containing all the split parts.

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

Send a POST request to `http://localhost:8000/split` with a file upload (form field name: `file`) and a form field `size` (in bytes).

Example using `curl`:
```bash
curl -F "file=@path/to/your/file" -F "size=1024" http://localhost:8000/split --output split_parts.tar
```

This will return a tar archive containing the split parts as files named `part_1`, `part_2`, etc. 