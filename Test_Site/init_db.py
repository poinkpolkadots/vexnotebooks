import os
import psycopg2

conn = psycopg2.connect(
    host = "drhscit.org",
    database = os.environ['DB'],
    user = os.environ['DB_UN'],
    password = os.environ['DB_PW']
)

cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS reviews;')
cur.execute('CREATE TABLE reviews (id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,'
            'title VARCHAR(150) NOT NULL,'
            'author VARCHAR(50) NOT NULL,'
            'pages INTEGER,'
            'review TEXT,'
            'date DATE DEFAULT CURRENT_DATE NOT NULL);'
                                )

conn.commit()

cur.close()
conn.close()