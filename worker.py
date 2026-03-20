import time
from util import *

def run() -> None:
    while True: #runs forever
        #print('scanning') #NOTE may or may not be desired, since this will print every 5 seconds
        try: #prevent from crashing
            for row in select('pending'): #for each pdf w/o indexes,
                id = row[0]
                print(f'start embedding for pdf {id}')
                update(id, 'embedding') #set it's status to embedding
                create_idx(id) #create the idx
                update(id, 'embedded') #update the status to complete
                print(f'finished embedding for pdf {id}')
            for row in select('embedded'): #for each pdf with indexes,
                id = row[0]
                print(f'start querying for pdf {id}')
                update(id, 'processing') #update the status to processing
                query_and_write_all(id) #write the results of the queries to the res file
                update(id, 'completed') #update the status to complete
                print(f'finished querying for pdf {id}')
        except Exception as e: #if any error happens
            print(e) #print it out
            time.sleep(10) #wait a bit longer
        time.sleep(5) #wait 5 seconds between each loop

def select(status: str) -> list: #returns rows with a specific status
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id FROM registry WHERE status = %s;", (status,))
    rows = cur.fetchall()
    cur.close()
    con.close()
    return rows

def update(id: int, status: str) -> None: #updates the status of a row by id
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("UPDATE registry SET status = %s WHERE id = %s;", (status, id))
    con.commit()
    cur.close()
    con.close()

if __name__ == "__main__":
    run() #start the loop