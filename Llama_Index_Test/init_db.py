import os
import psycopg2

conn = psycopg2.connect(
    host = "drhscit.org",
    database = os.environ["DB"],
    user = os.environ["DB_UN"],
    password = os.environ["DB_PW"]
)

cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS notebooks;")
cur.execute("DROP TABLE IF EXISTS notebooks;"
            "CREATE TABLE notebooks ("
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "notebook_name TEXT,"
            "pdf_path TEXT,"
            "output TEXT,"
            "date DATE DEFAULT CURRENT_DATE);"
            )

conn.commit()
cur.close()
conn.close()