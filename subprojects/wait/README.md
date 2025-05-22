# Wait FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/wait` to wait for a specified number of seconds.

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

Send a POST request to `http://localhost:8000/wait` with a JSON body:

```
{
  "wait_time": 2.5
}
```

Response:
```
{
  "waited": true
}
``` 