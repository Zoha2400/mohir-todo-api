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
    return jsonify('Hello World');

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

    if not user_uid or not user_jwt or not email:
        return jsonify({'error': 'Missing required fields'}), 400

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                cursor.execute("SELECT * FROM projects WHERE creator = %s", (user_uid,))
                rows = cursor.fetchall()
                conn.commit()
                return jsonify(rows)
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400


                    

@app.route('/get_todos')
def get_todos():
    data = request.json
    user_uid = data.get('user_uid')
    user_jwt = data.get('jwt_key')
    email = data.get('email')

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                cursor.execute("SELECT * FROM todos WHERE creator = %s", (user_uid,))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows)
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400


@app.route('/checked')
def check():
    data = request.json
    user_uid = data.get('user_uid')
    todo_id = data.get('todo_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')


    if not user_uid or not todo_id or not email or not user_jwt:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                query = """
                    WITH updated AS (
                        UPDATE todos
                        SET status = NOT status
                        WHERE todo_uid = %s AND creator = %s
                        RETURNING *
                    )
                    SELECT * FROM updated
                    UNION ALL
                    SELECT * FROM todos WHERE creator = %s AND todo_uid != %s;
                """
                cursor.execute(query, (todo_id, user_uid, user_uid, todo_id))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400


@app.route('/delete_todo', methods=['DELETE'])
def delete_todo():
    data = request.json
    user_uid = data.get('user_uid')
    todo_uid = data.get('todo_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')

    if not user_uid or not todo_uid or not email or not user_jwt:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                # Удаление задачи
                cursor.execute("DELETE FROM todos WHERE todo_uid = %s AND creator = %s RETURNING *;", (todo_uid, user_uid))
                deleted_rows = cursor.fetchall()
                conn.commit()

                if not deleted_rows:
                    return jsonify({'error': 'Todo item not found or not authorized'}), 404

                # Выборка оставшихся задач
                cursor.execute("SELECT * FROM todos WHERE creator = %s;", (user_uid,))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400



@app.route('/delete_project', methods=['DELETE'])
def delete_project():

    data = request.json
    user_uid = data.get('user_uid')
    project_uid = request.json.get('project_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')

    if not user_uid or not project_uid or not email or not user_jwt:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                # Удаление задачи
                cursor.execute("DELETE FROM projects WHERE project_uid = %s AND creator = %s RETURNING *;", (project_uid , user_uid))
                deleted_rows = cursor.fetchall()
                conn.commit()

                if not deleted_rows:
                    return jsonify({'error': 'project item not found or not authorized'}), 404

                # Выборка оставшихся задач
                cursor.execute("SELECT * FROM projects WHERE creator = %s;", (user_uid,))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400



@app.route('/change_todo', methods=["POST"])
def change_todo():
    data = request.json
    user_uid = data.get('user_uid')
    todo_uid = data.get('todo_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')
    text = data.get('text')


    if not user_uid or not todo_uid or not email or not user_jwt or not text:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                query = """
                    WITH updated AS (
                        UPDATE todos
                        SET text = %s
                        WHERE todo_uid = %s AND creator = %s
                        RETURNING *
                    )
                    SELECT * FROM updated
                    UNION ALL
                    SELECT * FROM todos WHERE creator = %s AND todo_uid = %s;
                """
                cursor.execute(query, (text, todo_uid, user_uid, user_uid, todo_uid))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400




@app.route('/change_project_name', methods=["POST"])
def change_project_name():
    data = request.json
    user_uid = data.get('user_uid')
    project_uid = data.get('project_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')
    project_name = data.get('project_name')

    if not user_uid or not project_uid or not email or not user_jwt or not project_name:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                query = """
                    WITH updated AS (
                        UPDATE projects
                        SET name = %s
                        WHERE project_uid = %s AND creator = %s
                        RETURNING *
                    )
                    SELECT * FROM updated
                    UNION ALL
                    SELECT * FROM projects WHERE creator = %s AND project_uid = %s;
                """
                cursor.execute(query, (project_name, project_uid, user_uid, user_uid, project_uid))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400



@app.route('/change_project_description')
def change_project_description():
    data = request.json
    user_uid = data.get('user_uid')
    project_uid = data.get('project_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')
    description = data.get('description')

    if not user_uid or not project_uid or not email or not user_jwt or not description:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                query = """
                    WITH updated AS (
                        UPDATE projects
                        SET description = %s
                        WHERE project_uid = %s AND creator = %s
                        RETURNING *
                    )
                    SELECT * FROM updated
                    UNION ALL
                    SELECT * FROM projects WHERE creator = %s AND project_uid = %s;
                """
                cursor.execute(query, (project_name, project_uid, user_uid, user_uid, project_uid))
                rows = cursor.fetchall()
                conn.commit()

                return jsonify(rows), 200
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400



@app.route('/create_project')
def create_project():
    data = request.json
    user_uid = data.get('user_uid')
    project_uid = data.get('project_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')
    project_name = data.get('project_name')
    description = data.get('description')

    if not user_uid or not project_uid or not email or not user_jwt or not description or not project_name:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                cursor.execute("""INSERT INTO projects (name, creator, description) VALUES (%s, %s, %s) RETURNING *""",
                               (project_name, user_uid, description))
                new_project = cursor.fetchone()
                conn.commit()
                
                if new_project:
                    cursor.execute("SELECT * FROM projects WHERE creator = %s", (user_uid,))
                    rows = cursor.fetchall()
                    conn.commit()
                    return jsonify(rows), 201
                else:
                    return jsonify({'error': 'Failed to add project'}), 500
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400



@app.route('/create_todo', methods=["POST"])
def create_todo():

    data = request.json
    user_uid = data.get('user_uid')
    project_uid = data.get('project_uid')
    email = data.get('email')
    user_jwt = data.get('jwt_key')
    text = data.get('text')



    if not user_uid or not project_uid or not email or not user_jwt or not text:
        return jsonify({'error': 'Missing required fields'}), 401

    jwt_cached = r.get(email)

    if jwt_cached:
        jwt_val = key_validation(user_jwt.encode('utf-8'), jwt_cached.encode('utf-8'))

        if jwt_val == 1:
            try:
                cursor.execute("""INSERT INTO todos (todo_project, creator, text) VALUES (%s, %s, %s) RETURNING *""",
                               (project_uid, user_uid, text))
                new_todo = cursor.fetchone()
                conn.commit()
                
                if new_todo:
                    cursor.execute("SELECT * FROM todos WHERE creator = %s", (user_uid,))
                    rows = cursor.fetchall()
                    conn.commit()
                    return jsonify(rows), 201
                else:
                    return jsonify({'error': 'Failed to add todo'}), 500
            except psycopg2.Error as e:
                conn.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify("Incorrect Token/Token expired"), 400
    else:
        return jsonify("No cached JWT found"), 400


if __name__ == "__main__":
    app.run(debug=True)
