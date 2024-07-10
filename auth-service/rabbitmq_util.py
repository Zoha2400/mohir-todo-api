import pika
import json


def send_to_queue(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='user_events')
    channel.basic_publish(exchange='', routing_key='user_events', body=json.dumps(message))
    connection.close()

