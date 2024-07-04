import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="hundproj",
        user="postgres",
        password="05350535"
    )
    return conn


def get_db_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)

