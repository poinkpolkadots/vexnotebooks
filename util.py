import fitz, os, shutil, psycopg2

STORAGE = "C:\\vexnotebooks"

def pdf_to_text(path): #convert PDF to text
    doc = fitz.open(path) #open the PDF document
    text = ""
    for page_num in range(len(doc)): #iterate through each page
        page = doc.load_page(page_num) #load the page
        text += f"\npage {page_num + 1}\n" + page.get_text() #extract text and add to string
    doc.close() #close the PDF document
    return text #return the extracted text

def get_db_connection():
    return psycopg2.connect( #defaults for local testing
        host="drhscit.org",
        database=os.environ['DB'],
        user=os.environ['DB_UN'],
        password=os.environ['DB_PW']
    )

def reset():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DROP TABLE IF EXISTS registry;"
        "CREATE TABLE registry ("
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "name VARCHAR(255) NOT NULL,"
            "pdf_path TEXT NOT NULL,"
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ");"
    )
    conn.commit()
    cur.close()
    conn.close()

    if os.path.exists(STORAGE):
        shutil.rmtree(STORAGE)
    os.makedirs(os.path.join(STORAGE, "pdf"), exist_ok=True)
    os.makedirs(os.path.join(STORAGE, "txt"), exist_ok=True)