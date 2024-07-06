import pika
import json
from postgres import get_db_connection, get_db_cursor  # Импортируем функции для работы с PostgreSQL

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'mohirtodo'

# Функция для отправки сообщения в очередь RabbitMQ
def send_to_queue(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()

    # Объявляем очередь с параметром durable=True для сохранения сообщений при перезапуске RabbitMQ
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Публикуем сообщение в очередь
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=json.dumps(message),  # Преобразуем сообщение в JSON формат
        properties=pika.BasicProperties(
            delivery_mode=2  # Делаем сообщение персистентным (сохраняемое)
        )
    )
    connection.close()  # Закрываем соединение с RabbitMQ

# Функция для обработки сообщений из очереди RabbitMQ
def callback(ch, method, properties, body):
    message = json.loads(body)  # Преобразуем JSON строку обратно в объект Python
    query = message['query']  # Извлекаем SQL запрос из сообщения
    
    conn = get_db_connection()  # Устанавливаем соединение с базой данных PostgreSQL
    cursor = get_db_cursor(conn)  # Получаем курсор для выполнения SQL запросов
    
    try:
        cursor.execute(query)  # Выполняем SQL запрос
        result = cursor.fetchall()  # Получаем результат выполнения запроса
        print(result)  # Выводим результат на консоль (для демонстрации)
    except Exception as e:
        print(f"Error executing query: {e}")  # Выводим сообщение об ошибке, если есть исключение
    finally:
        conn.close()  # Закрываем соединение с базой данных
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Подтверждаем успешную обработку сообщения

# Функция для начала прослушивания (потребления) сообщений из очереди RabbitMQ
def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    
    # Объявляем очередь с параметром durable=True для сохранения сообщений при перезапуске RabbitMQ
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    channel.basic_qos(prefetch_count=1)  # Устанавливаем предварительное количество сообщений (prefetch_count)
    
    # Начинаем потребление (прослушивание) сообщений из очереди с использованием функции callback для их обработки
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    
    channel.start_consuming()  # Запускаем бесконечный цикл обработки сообщений

# Все функции выглядят правильно написанными. Важно убедиться, что настройки RabbitMQ и PostgreSQL корректны и доступны.
