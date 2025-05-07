# MegaAPIs Project

This repository contains three FastAPI-based subprojects, each in its own self-contained directory under `subprojects/`:

- **addition**: A FastAPI app with a single POST endpoint `/add` that adds two numbers.
- **subtraction**: A FastAPI app with a single POST endpoint `/subtract` that subtracts one number from another.
- **api**: A FastAPI app with a single POST endpoint `/calculate` that takes a number, adds a random number (using the addition service), then subtracts a random number (using the subtraction service), and returns the result. The addition and subtraction service URLs are configurable via environment variables.

## Running All Services with Docker Compose

To build and run all three services together, use Docker Compose:

```bash
# From the root of the repository
docker-compose up --build
```

- The main API (`/calculate`) will be available at [http://localhost:8000/calculate](http://localhost:8000/calculate)
- The addition service (`/add`) will be available at [http://localhost:8001/add](http://localhost:8001/add)
- The subtraction service (`/subtract`) will be available at [http://localhost:8002/subtract](http://localhost:8002/subtract)

## Example Usage

To call the main API's `/calculate` endpoint:

```bash
curl -X POST http://localhost:8000/calculate -H "Content-Type: application/json" -d '{"x": 5}'
```

## Customizing Service URLs

You can override the addition and subtraction service URLs for the `api` service by setting the `ADDITION_URL` and `SUBTRACTION_URL` environment variables in the Docker Compose file or your environment.

---

Each subproject also contains its own README with standalone run instructions if you want to run them individually.
