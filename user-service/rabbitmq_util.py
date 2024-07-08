import pika
import json
from postgres import get_db_connection, get_db_cursor

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'mohirtodo'

def send_to_queue(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=QUEUE_NAME,
                          body=json.dumps(message),
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          ))

    connection.close()


def callback(ch, method, properties, body):
    message = json.loads(body)
    query = message['query']
    
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    try:
        cursor.execute(query)
        conn.commit()  # Не забудьте сохранить изменения в базе данных
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        cursor.close()
        conn.close()
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()



