# Subtraction FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/subtract` to subtract two numbers.

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

Send a POST request to `http://localhost:8000/subtract` with a JSON body:

```
{
  "a": 5.0,
  "b": 2.0
}
```

Response:
```
{
  "result": 3.0
}
``` 