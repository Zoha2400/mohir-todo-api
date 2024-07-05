from flask import Flask, jsonify, request, send_file
import psycopg2
from postgres import get_db_connection, get_db_cursor
from jwt_util import generate_jwt
import bcrypt
import redis

app = Flask(__name__)
cursor = None
conn = None
r = None


@app.before_request
def before_request():
    global cursor, conn, r
    conn = get_db_connection()
    cursor = get_db_cursor(conn)
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


@app.route('/')
def index():
    # cursor.execute('SELECT * FROM products')
    # rows = cursor.fetchall()
    token = generate_jwt('78679ewqewq')
    return jsonify({'token': token})


@app.route('/user')
def user():
    cursor.execute('SELECT * FROM user_accounts')
    rows = cursor.fetchall()

    return jsonify(rows)


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
            return jsonify({
                'message': 'User registered successfully'
            }), 201
        except psycopg2.Error as e:
            conn.rollback()  # Откат транзакции в случае ошибки
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'This email is already registered!'}), 400


@app.route('/login')
def login():
    email = request.json.get('email')
    password = request.json.get('password')


@app.route('/get_projects/<string:jwt_key>')
def get_projects(jwt_key):
    user_uid = request.json.get('user_uid')
    try:
        # Тут будет проверка с редисом
        cursor.execute("SELECT * FROM projects WHERE creator = %s", (user_uid))
        rows = cursor.fetchall()
        conn.commit()

        return jsonify(rows)

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/get_todos/<string:jwt_key>')
def get_todos(jwt_key):
    user_uid = request.json.get('user_uid')
    try:
        # Тут будет проверка с редисом
        cursor.execute("SELECT * FROM todos WHERE creator = %s", (user_uid))
        rows = cursor.fetchall()
        conn.commit()

        return jsonify(rows)

    except psycopg2.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/check/<string:jwt_key>')
def check(jwt_key):
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
