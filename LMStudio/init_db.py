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
        "DROP TABLE IF EXISTS main;"
        "CREATE TABLE main ("
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "image BYTEA,"
            "mimetype VARCHAR(100),"
            "date DATE DEFAULT CURRENT_DATE NOT NULL"
        ");"
    )

    conn.commit()

    cur.close()
    conn.close()

init()