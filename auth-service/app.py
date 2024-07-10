from flask import Flask, jsonify, request, send_file
import psycopg2
from postgres import get_db_connection, get_db_cursor
from jwt_util import generate_jwt
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from rabbitmq_util import send_to_queue
from flask_cors import CORS

app = Flask(__name__)
cursor = None
conn = None
r = None


CORS(app)
           
# Подключение к RabbitMQ


@app.before_request
def before_request():
    global cursor, conn, r
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)



@app.route('/auth/')
def helloAuth():
    return jsonify("Hello from auth!")


@app.route('/auth/register', methods=['POST'])
def register():
    try:
        name = request.json.get('name')
        password = request.json.get('password')
        email = request.json.get('email')
        age = request.json.get('age')

        if not name or not password or not email or not age:
            return jsonify({'error': 'Missing required fields'}), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        cursor.execute("SELECT email FROM users WHERE email = %s;", (email,))
        result = cursor.fetchall()

        if not result:
            cursor.execute("""INSERT INTO users (name, email, password, age) VALUES (%s, %s, %s, %s);""",
                           (name, email, hashed_password, age))
            conn.commit()

            r.setex(email, 3600, generate_jwt(name))

            send_to_queue({'event': 'user_registered', 'user_name': name, 'email': email})

            return jsonify({'message': 'Registration successful'}), 200
        else:
            return jsonify({'error': 'This email is already registered!'}), 400

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error: ' + str(e)}), 500




@app.route('/auth/login', methods=['GET'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error':'Missing required fields'}), 400
    
    cursor.execute("SELECT * FROM users WHERE email = %s;", (email,))
    result = cursor.fetchone()

    # return jsonify(result[0]["password"])

    if not result:
        return jsonify('Email was not found'), 400
    
    cursor.execute("SELECT uid FROM users WHERE email = %s", (email,))
    user_uid = cursor.fetchone()
    
    hashed_password = check_password_hash(result['password'], password) 

    if hashed_password:
              return jsonify(
                {
                    'email': email,
                    'jwt_key': r.get(email),
                    'uid': user_uid['uid']
                }
            ), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401



if __name__ == "__main__":
    app.run(debug=True) 

    

