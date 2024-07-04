from flask import Flask, jsonify, request, send_file
import psycopg2
from postgres import get_db_connection, get_db_cursor
from flask_swagger_ui import get_swaggerui_blueprint
import bcrypt


app = Flask(__name__)
cursor = None
conn = None


@app.before_request
def before_request():
    global cursor, conn
    conn = get_db_connection()
    cursor = get_db_cursor(conn)


@app.route('/')
def index():
    cursor.execute('SELECT * FROM products')
    rows = cursor.fetchall()

    return jsonify(rows)


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
            return jsonify({'message': 'User registered successfully'}), 201
        except psycopg2.Error as e:
            conn.rollback()  # Откат транзакции в случае ошибки
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'This email is already registered!'}), 400





# @app.route('/login')
#
# @app.route('/get_projects/<string:id>')
#
# @app.route('/get_todos/<string:id>')
#
# @app.route('/check/<string:id>')
#
# @app.route('/delete/<string:id')
#
# @app.route('/change/<string:id>')
#
# @app.route('/create_project/<string:id>')
#
# @app.route('/create_todo/<string:id>')
#
# @app.route('/invite/<string:id>')


if __name__ == "__main__":
    app.run(debug=True)
