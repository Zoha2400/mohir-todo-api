from flask import Flask, jsonify, request, Response, send_file
import psycopg2
from postgres import get_db_connection, get_db_cursor
from jwt_util import generate_jwt, key_validation
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

    channel.queue_declare('mohirtodo', durable=True)


def redis_token(email, name):
    r.setex(email, 28800, name)




@app.before_request
def before_request():
    global cursor, conn, r
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


    rabbit_connect()


@app.route('/')
def jwtG():
    email = request.json.get("email");
    return generate_jwt(email)

@app.route('/user')
def user():
    cursor.execute('SELECT * FROM user_accounts')
    rows = cursor.fetchall()

    return jsonify(rows)



@app.route('/get_projects', methods=['GET'])
def get_projects():
    data = request.json
    user_uid = data.get('user_uid')
    user_jwt = data.get('jwt_key')
    email = data.get('email')

    jwt_chached = r.get(email)


    jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_chached.encode('utf-8'))
    
    if jwt_val == 1:
        try:
            
            cursor.execute("SELECT * FROM projects WHERE creator = %s", (user_uid,))
            rows = cursor.fetchall()
            conn.commit()
            
            return jsonify(rows)

        except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
    elif jwt_val == 0:
        return jsonify("Incorrect Token"), 400
    elif jwt_val == 3:
        return jsonify("Fake Token!"), 400
    else:
        r.set(email, generate_jwt(user_uid))
        return get_projects()
            



@app.route('/get_todos')
def get_todos():
    data = request.json
    user_uid = data.get('user_uid')
    user_jwt = data.get('jwt_key')
    email = data.get('email')

    jwt_chached = r.get(email)


    jwt_val = key_validation(user_jwt, jwt_chached)
    
    if jwt_val == 1:
        try:
            cursor.execute("SELECT * FROM todos WHERE creator = %s", (user_uid,))
            rows = cursor.fetchall()
            conn.commit()

            return jsonify(rows)

        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
    elif jwt_val == 0:
        return jsonify("Incorrect Token"), 400
    elif jwt_val == 3:
        return jsonify("Fake Token!"), 400
    else:
        r.set(email, generate_jwt(user_uid))
        return get_projects()



@app.route('/checked')
def check():
    user_uid = request.json.get('user_uid')
    todo_id = request.json.get('todo_id')
    # Проверка jwt в redis
    try :
        cursor.execute("UPDATE todos SET status = TRUE WHERE todo_id = %s AND creator = %s", (todo_id, user_uid))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/delete_todo/<string:jwt_key>')
def delete_todo(jwt_key):
    user_uid = request.json.get('user_uid')
    todo_id = request.json.get('todo_id')
    # Проверка jwt в redis
    try:
        cursor.execute("DELETE * FROM todos WHERE todo_id = %s AND creator = %s", (todo_id, user_uid))
        conn.commit()

        return "Deleted"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/delete_project/<string:jwt_key>')
def delete_project(jwt_key):
    user_uid = request.json.get('user_uid')
    project_uid = request.json.get('project_uid')
    # Проверка jwt в redis
    try:
        cursor.execute("DELETE * FROM projects WHERE project_uid  = %s AND creator = %s", (project_uid, user_uid))
        cursor.execute("DELETE * FROM todos WHERE todo_project = %s AND creator = %s", (project_uid, user_uid))
        conn.commit()

        return "Deleted"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/change_todo/<string:jwt_key>')
def change_todo(jwt_key):
    user_uid = request.json.get('user_uid')
    todo_id = request.json.get('todo_id')
    text = request.json.get('text')
    # Проверка jwt в redis
    try :
        cursor.execute("UPDATE todos SET text = %s WHERE todo_id = %s AND creator = %s", (text, todo_id, user_uid))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/change_project_name/<string:jwt_key>')
def change_project_name(jwt_key):
    user_uid = request.json.get('user_uid')
    project_uid = request.json.get('project_uid')
    project_name = request.json.get('project_name')
    # Проверка jwt в redis
    try :
        cursor.execute("UPDATE projects SET name = %s WHERE todo_id = %s AND creator = %s",
                       (project_name, project_uid, user_uid))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/change_project_description/<string:jwt_key>')
def change_project_description(jwt_key):
    user_uid = request.json.get('user_uid')
    project_uid = request.json.get('project_uid')
    description = request.json.get('description')
    # Проверка jwt в redis
    try:
        cursor.execute("UPDATE projects SET description = %s WHERE todo_id = %s AND creator = %s",
                       (description, project_uid, user_uid))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/create_project/<string:jwt_key>')
def create_project(jwt_key):
    user_uid = request.json.get('user_uid')
    project_name = request.json.get('project_name')
    description = request.json.get('description')
    # Проверка jwt в redis
    try:
        cursor.execute("""INSERT INTO projects (name, creator, description) VALUES (%s, %s, %s)""",
                       (project_name, user_uid, description))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/create_todo/<string:jwt_key>')
def create_todo(jwt_key):
    user_uid = request.json.get('user_uid')
    project_uid = request.json.get('project_uid')
    text = request.json.get('text')
    # Проверка jwt в redis
    try:
        cursor.execute("""INSERT INTO todos (project_uid, text, user_uid ) VALUES (%s, %s, %s)""",
                       (project_uid, text, user_uid))
        conn.commit()

        return "Changed"

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
