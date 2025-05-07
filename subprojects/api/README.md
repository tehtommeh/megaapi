# API FastAPI Subproject

This is a self-contained FastAPI application that provides a single POST endpoint `/calculate` to process a number.

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

Send a POST request to `http://localhost:8000/calculate` with a JSON body:

```
{
  "x": 7.0
}
```

Response (placeholder logic returns the same number):
```
{
  "result": 7.0
}
``` 