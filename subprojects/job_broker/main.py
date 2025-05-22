from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import pika
import uuid
import json
import os
import time
from typing import Optional
from enum import Enum
import redis

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# --- Models ---
class SubmitRequest(BaseModel):
    payload: dict

class SubmitResponse(BaseModel):
    task_id: str

class CompleteRequest(BaseModel):
    result: dict

class FetchJobResponse(BaseModel):
    task_id: str
    payload: dict

# --- Task State Enum ---
class TaskState(str, Enum):
    completed = "completed"
    queued = "queued"
    expired = "expired"
    missing = "missing"

class StatusResponse(BaseModel):
    task_id: str
    state: TaskState  # completed | queued | missing

class ResultResponse(BaseModel):
    task_id: str
    state: TaskState
    result: Optional[dict]

# --- Queue Name Templates ---
TASK_QUEUE_TEMPLATE = "task_queue:{task_type}"
PROCESSING_DELAY_QUEUE_TEMPLATE = "processing_delay:{task_type}"
RESULT_QUEUE_TEMPLATE = "result_queue:{task_type}"
DLQ_QUEUE_TEMPLATE = "task_queue:{task_type}:dlq"

def task_queue_name(task_type):
    return TASK_QUEUE_TEMPLATE.format(task_type=task_type)

def processing_delay_queue_name(task_type):
    return PROCESSING_DELAY_QUEUE_TEMPLATE.format(task_type=task_type)

def result_queue_name(task_type):
    return RESULT_QUEUE_TEMPLATE.format(task_type=task_type)

def dlq_queue_name(task_type):
    return DLQ_QUEUE_TEMPLATE.format(task_type=task_type)

# --- RabbitMQ Helpers ---
def get_connection():
    while True:
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
        except pika.exceptions.AMQPConnectionError:
            print("Waiting for RabbitMQ...")
            time.sleep(2)

def declare_queues(channel, task_type):
    # Dead Letter Queue
    channel.queue_declare(queue=dlq_queue_name(task_type), durable=True)
    # Task queue with DLQ
    channel.queue_declare(
        queue=task_queue_name(task_type),
        durable=True,
        arguments={
            'x-message-ttl': 300000,  # 5 min
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': dlq_queue_name(task_type)
        }
    )
    # Processing delay queue (TTL, DLX)
    channel.queue_declare(
        queue=processing_delay_queue_name(task_type),
        durable=True,
        arguments={
            'x-message-ttl': 300000,  # 5 min
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': task_queue_name(task_type)
        }
    )
    # Result queue
    channel.queue_declare(queue=result_queue_name(task_type), durable=True)

# --- API Endpoints ---
@app.post("/submit/{task_type}", response_model=SubmitResponse)
def submit_job(task_type: str, req: SubmitRequest):
    task_id = str(uuid.uuid4())
    message = {
        "task_id": task_id,
        "task_type": task_type,
        "payload": req.payload,
        "result": None
    }
    conn = get_connection()
    channel = conn.channel()
    declare_queues(channel, task_type)
    channel.basic_publish(
        exchange='',
        routing_key=task_queue_name(task_type),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type='application/json',
        )
    )
    conn.close()
    return {"task_id": task_id}

@app.post("/fetch_job/{task_type}", response_model=FetchJobResponse)
def fetch_job(task_type: str):
    conn = get_connection()
    channel = conn.channel()
    declare_queues(channel, task_type)
    method, props, body = channel.basic_get(queue=task_queue_name(task_type), auto_ack=False)
    if not method:
        conn.close()
        raise HTTPException(status_code=404, detail="No pending jobs")
    message = json.loads(body)
    # Move to processing_delay queue (with TTL)
    channel.basic_publish(
        exchange='',
        routing_key=processing_delay_queue_name(task_type),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json',
        )
    )
    channel.basic_ack(method.delivery_tag)
    conn.close()
    return {"task_id": message["task_id"], "payload": message["payload"]}

@app.post("/complete/{task_type}/{task_id}")
def complete_job(task_type: str, task_id: str, req: CompleteRequest):
    conn = get_connection()
    channel = conn.channel()
    # Scan processing_delay queue for the task_id
    queue = processing_delay_queue_name(task_type)
    msg = None
    for _ in range(100):
        method, props, body = channel.basic_get(queue=queue, auto_ack=False)
        if not method:
            break
        candidate = json.loads(body)
        if candidate["task_id"] == task_id:
            msg = candidate
            channel.basic_ack(method.delivery_tag)
            break
        else:
            channel.basic_nack(method.delivery_tag, requeue=True)
    if not msg:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found in processing queue")
    # Publish to result_queue
    msg["result"] = req.result
    channel.basic_publish(
        exchange='',
        routing_key=result_queue_name(task_type),
        body=json.dumps(msg),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json',
        )
    )
    conn.close()
    return {"status": "ok"}

@app.get("/status/{task_type}/{task_id}", response_model=StatusResponse)
def get_status(task_type: str, task_id: str):
    # 1. Check if result exists in Redis
    result = redis_client.get(f"job:{task_id}:result")
    if result:
        return {"task_id": task_id, "state": TaskState.completed}
    # 2. Check if job is in the queue (pending or processing)
    conn = get_connection()
    channel = conn.channel()
    found = False
    for queue in [task_queue_name(task_type), processing_delay_queue_name(task_type)]:
        for _ in range(10):  # small scan limit
            method, props, body = channel.basic_get(queue=queue, auto_ack=False)
            if not method:
                break
            msg = json.loads(body)
            if msg["task_id"] == task_id:
                channel.basic_nack(method.delivery_tag, requeue=True)
                conn.close()
                return {"task_id": task_id, "state": TaskState.queued}
            channel.basic_nack(method.delivery_tag, requeue=True)
    # 3. Check DLQ for expired/dropped jobs
    dlq = dlq_queue_name(task_type)
    for _ in range(10):
        method, props, body = channel.basic_get(queue=dlq, auto_ack=False)
        if not method:
            break
        msg = json.loads(body)
        if msg["task_id"] == task_id:
            channel.basic_nack(method.delivery_tag, requeue=True)
            conn.close()
            return {"task_id": task_id, "state": TaskState.expired}
        channel.basic_nack(method.delivery_tag, requeue=True)
    conn.close()
    # 4. Otherwise, missing
    return {"task_id": task_id, "state": TaskState.missing}

@app.get("/result/{task_type}/{task_id}", response_model=ResultResponse)
def get_result(task_type: str, task_id: str):
    conn = get_connection()
    channel = conn.channel()
    queue = result_queue_name(task_type)
    for _ in range(100):
        method, props, body = channel.basic_get(queue=queue, auto_ack=False)
        if not method:
            break
        msg = json.loads(body)
        if msg["task_id"] == task_id:
            channel.basic_nack(method.delivery_tag, requeue=True)
            conn.close()
            return {"task_id": task_id, "state": TaskState.complete, "result": msg["result"]}
        else:
            channel.basic_nack(method.delivery_tag, requeue=True)
    conn.close()
    raise HTTPException(status_code=404, detail="Result not found")

# --- Notes ---
# - For demo, task_types are hardcoded. In production, you may want to keep a registry or config of valid types.
# - Scanning queues is inefficient for large queues, but matches the design.
# - Error handling is basic; production code should be more robust.
