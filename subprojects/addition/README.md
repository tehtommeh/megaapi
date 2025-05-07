# Addition FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/add` to add two numbers.

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

Send a POST request to `http://localhost:8000/add` with a JSON body:

```
{
  "a": 1.5,
  "b": 2.5
}
```

Response:
```
{
  "result": 4.0
}
``` 