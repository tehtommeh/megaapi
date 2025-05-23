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

# Set to keep strong references to background tasks
background_tasks = set()

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
            webhook_url = headers.pop("x-async-webhook-url", None)

            async def process_request():
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        content=body,
                        headers=headers,
                        timeout=60
                    )
                    response_data = {
                        'content': response.content,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                    if webhook_url:
                        # POST the result to the webhook URL
                        await client.post(
                            webhook_url,
                            content=response.content,
                            headers={**response_data['headers'], 'X-Async-Job-Id': job_id}
                        )
                    else:
                        # Use Redis connection pool
                        redis_client = redis.Redis(connection_pool=redis_pool)
                        await redis_client.set(job_id, pickle.dumps(response_data))
                        await redis_client.close()

            task = asyncio.create_task(process_request())
            
            # Add the task to the set to keep it alive
            # This is necessary because the task will be garbage collected if not kept alive
            # https://docs.python.org/3/library/asyncio-task.html#creating-tasks
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            
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