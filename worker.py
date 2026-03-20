import time
from util import *

def run():
    while True:
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("SELECT id FROM registry WHERE status = 'pending';")
            row = cur.fetchone()
            if row:
                id = row[0]
                cur.execute("UPDATE registry SET status = 'processing' WHERE id = %s;", (id,))
                con.commit()
                query_and_write_all(id)
                cur.execute("UPDATE registry SET status = 'completed' WHERE id = %s;", (id,))
                con.commit()
            cur.close()
            con.close()
        except Exception as e:
            print(e)
            time.sleep(10)
        time.sleep(5)

if __name__ == "__main__":
    run()