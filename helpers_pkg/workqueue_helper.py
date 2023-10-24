from secrets_pkg.workqueue_secret import *
import pika
from pika.exceptions import AMQPConnectionError
from pika.adapters.blocking_connection import BlockingChannel
import logging


def connect_to_channel() -> BlockingChannel | None:
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL_PARAMS))
        channel = connection.channel()
        channel.queue_declare(queue='task_queue', durable=True)
    except AMQPConnectionError as exc:
        logging.error(exc)
        logging.error(exc.__cause__)
    else:
        return channel


def publish_task(channel: BlockingChannel, email: str) -> str | None:
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=email.encode('utf8'),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
    return None
