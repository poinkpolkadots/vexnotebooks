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
cur.execute("CREATE TABLE notebooks (id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "pdf BYTEA,"
            "mimetype VARCHAR(100),"
            "name TEXT NOT NULL,"
            "date DATE DEFAULT CURRENT_DATE NOT NULL,"
            "output LONGTEXT);"
                                )

conn.commit()
cur.close()
conn.close()