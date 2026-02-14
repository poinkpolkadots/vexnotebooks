import os, psycopg2

def get_db_connection():
    conn = psycopg2.connect( #defaults for local testing TODO: change to env variables later
        host="localhost",
        database="vexpdfs",
        user="postgres",
        password="1q2w3e4r"
    )
    return conn

def init():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DROP TABLE IF EXISTS registry;"
        "CREATE TABLE registry ("
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "name VARCHAR(255) NOT NULL,"
            "path TEXT NOT NULL,"
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ");"
    )

    conn.commit()

    cur.close()
    conn.close()

init()