from fastapi import FastAPI
import pika
import requests
import threading
import json
import os
import time

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
SERVICE_NAME = os.getenv("SERVICE_NAME", "addition")  # e.g., 'addition' or 'subtraction'
DOWNSTREAM_URL = os.getenv("DOWNSTREAM_URL", "http://addition:8000/add")  # Set via env

# TODO: Add authentication if needed

def process_queue():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
            break
        except pika.exceptions.AMQPConnectionError:
            print("Waiting for RabbitMQ in popper...")
            time.sleep(2)
    channel = connection.channel()
    queue_name = f"{SERVICE_NAME}_requests"
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, props, body):
        data = json.loads(body)
        # Forward the request to the real downstream API
        resp = requests.post(DOWNSTREAM_URL, json=data)
        resp_body = resp.json()
        # Publish the response to the reply queue
        channel.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id,
                content_type='application/json',
            ),
            body=json.dumps(resp_body)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()

@app.on_event("startup")
def start_background_worker():
    t = threading.Thread(target=process_queue, daemon=True)
    t.start()

# TODO: Add error handling, timeouts, and connection pooling 