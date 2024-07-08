from flask import Flask, jsonify, request, send_file
import psycopg2
from postgres import get_db_connection, get_db_cursor
from jwt_util import generate_jwt
import bcrypt
import redis
import pika
from rabbitmq_util import send_to_queue

app = Flask(__name__)
cursor = None
conn = None
r = None


# Подключение к RabbitMQ
def rabbit_connect():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare('auth_mohir', durable=True)


def redis_token(email, name):
    r.setex(email, 28800, name)




@app.before_request
def before_request():
    global cursor, conn, r
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    rabbit_connect()




@app.route('/registrate', methods=['POST'])
def registrate():
    name = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    age = request.json.get('age')

    if not name or not password or not email or not age:
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("SELECT email FROM users WHERE email = %s;", (email,))
    result = cursor.fetchall()
    if not result:
        try:
            cursor.execute("""INSERT INTO users (name, email, password, age) VALUES (%s, %s, %s, %s);""",
                           (name, email, hashed_password, age))

            conn.commit()  # Подтверждение транзакции

            r.setex(email, 3600, generate_jwt(name))
      
            return jsonify({
                'jwt': r.get(email)
            }), 201
        except psycopg2.Error as e:
            conn.rollback()  # Откат транзакции в случае ошибки
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'This email is already registered!'}), 400



@app.route('/login', methods=['GET'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error':'Missing required fields'}), 400
    
    cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
    result = cursor.fetchall()

    # return jsonify(result[0]["password"])

    if not result:
        return jsonify('Email was not found'), 400
    
    
    hashed_password = result[0]["password"].encode('utf-8')

    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401



if __name__ == "__main__":
    app.run(debug=True) 

    

