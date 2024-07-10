import pika
import json

def callback(ch, method, properties, body):
    message = json.loads(body)
    if message['event'] == 'user_registered':
        #отправка письма на почту пользователя по эмейлу
        print('done')

def listen_to_queue():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel

    channel.queue_declare(queue='user_events')
    channel.basic_consume(queue='user_events', on_message_callback = callback, auto_act = True) 
    channel.start_consuming()


