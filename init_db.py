import os, psycopg2

pdf_folder = "C:\\vexpdfs"

def get_db_connection():
    conn = psycopg2.connect( #defaults for local testing TODO: change to env variables later
        host="localhost",
        database="vexpdfs",
        user="postgres",
        password="1q2w3e4r"
    )
    return conn

def clear_folder():
    for name in os.listdir(pdf_folder):
        os.unlink(os.path.join(pdf_folder, name))

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

    clear_folder()