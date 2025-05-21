from functools import lru_cache
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_fastapi_instrumentator import Instrumentator
import uuid
import asyncio
import redis.asyncio as redis
import httpx
import pickle

# Create a Redis connection pool at module level
redis_pool = redis.ConnectionPool(host='redis', port=6379, decode_responses=False)


@lru_cache
def get_app() -> FastAPI:
    app = FastAPI()
    Instrumentator().instrument(app).expose(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def handle_async_request(request: Request, call_next):
        if request.headers.get("X-Async-Request", "").lower() == "true":
            job_id = str(uuid.uuid4())
            body = await request.body()
            method = request.method
            url = str(request.url)
            headers = dict(request.headers)
            headers.pop("x-async-request", None)  # Remove async header to avoid recursion

            async def process_request():
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        content=body,
                        headers=headers,
                    )
                    # Store only the response content and status code
                    response_data = {
                        'content': response.content,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                    # Use Redis connection pool
                    redis_client = redis.Redis(connection_pool=redis_pool)
                    await redis_client.set(job_id, pickle.dumps(response_data))
                    await redis_client.close()

            asyncio.create_task(process_request())
            return JSONResponse(content={"job_id": job_id})

        return await call_next(request)

    @app.get("/job_result/{job_id}")
    async def get_job_result(job_id: str):
        redis_client = redis.Redis(connection_pool=redis_pool)
        result = await redis_client.get(job_id)
        await redis_client.close()
        if result is None:
            return JSONResponse(status_code=404, content={"error": "Result not found"})
        response_data = pickle.loads(result)
        return Response(
            content=response_data['content'],
            status_code=response_data['status_code'],
            headers=response_data['headers']
        )

    return app