import time
from util import *

def run():
    while True: #runs forever
        #print('scanning') #NOTE may or may not be desired, since this will print every 5 seconds
        try: #prevent from crashing
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("SELECT id FROM registry WHERE status = 'pending';")
            rows = cur.fetchall() #select all the pdfs w/o indexes
            for row in rows: #for each pdf,
                id = row[0]
                print(f'start embedding for pdf {id}')
                cur.execute("UPDATE registry SET status = 'embedding' WHERE id = %s;", (id,))
                con.commit() #set it's status to embedding
                create_idx(id) #create the idx
                cur.execute("UPDATE registry SET status = 'embedded' WHERE id = %s;", (id,))
                con.commit() #update the status to complete
                print(f'finished embedding for pdf {id}')
            cur.execute("SELECT id FROM registry WHERE status = 'embedded';")
            rows = cur.fetchall() #select all pdfs with indexes
            for row in rows: #for each pdf,
                id = row[0]
                print(f'start querying for pdf {id}')
                cur.execute("UPDATE registry SET status = 'processing' WHERE id = %s;", (id,))
                con.commit() #update the status to processing
                query_and_write_all(id) #write the results of the queries to the res file
                cur.execute("UPDATE registry SET status = 'completed' WHERE id = %s;", (id,))
                con.commit() #update the status to complete
                print(f'finished querying for pdf {id}')
            cur.close()
            con.close()
        except Exception as e: #if any error happens
            print(e) #print it out
            time.sleep(10) #wait a bit longer
        time.sleep(5) #wait 5 seconds between each loop

if __name__ == "__main__":
    run()