from fastapi import FastAPI, Request
import pika
import uuid
import json
import os
import time

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

# TODO: Add authentication if needed

@app.post("/proxy/{service}")
async def proxy(service: str, request: Request):
    body = await request.json()
    correlation_id = str(uuid.uuid4())
    reply_queue = f"reply_{correlation_id}"

    # Retry logic for RabbitMQ connection
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
            break
        except pika.exceptions.AMQPConnectionError:
            print("Waiting for RabbitMQ in pusher...")
            time.sleep(2)
    channel = connection.channel()

    # Declare reply queue (auto-delete)
    channel.queue_declare(queue=reply_queue, exclusive=True, auto_delete=True)

    # Publish request to service queue
    channel.basic_publish(
        exchange='',
        routing_key=f"{service}_requests",
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=correlation_id,
            content_type='application/json',
        ),
        body=json.dumps(body)
    )

    # Wait for response
    response = None
    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == correlation_id:
            response = json.loads(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

    channel.basic_consume(queue=reply_queue, on_message_callback=on_response, auto_ack=False)
    channel.start_consuming()

    channel.queue_delete(queue=reply_queue)
    connection.close()

    return response

# TODO: Add error handling, timeouts, and connection pooling 