from flask import Flask, jsonify, request, resp
from postgres import get_db_connection, get_db_cursor
import bcrypt

app = Flask(__name__)

cursor = None


@app.before_request
def before_request():
    global cursor
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
    name = request.args.get('username')
    password = request.args.get('password')
    email = request.args.get('email')
    age = request.args.get('age')

    hashed_password = bcrypt.hashpw(password.encode('uft-8'), bcrypt.gensalt());
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    result = cursor.fetchall()

    if not result:
        cursor.execute("""INSERT INTO users (name, email, password, age) VALUES(%s, %s, %s);""", (name, email, hashed_password, age))
    else:
        return "This email is already registered!"

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
