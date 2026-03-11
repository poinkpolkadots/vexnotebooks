import fitz, os, shutil, psycopg2, uuid
from werkzeug.utils import secure_filename

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on

def pdf_to_text(path): #convert PDF to text
    doc = fitz.open(path) #open the PDF document
    text = ""
    for page_num in range(len(doc)): #iterate through each page
        page = doc.load_page(page_num) #load the page
        text += f"\npage {page_num + 1}\n" + page.get_text() #extract text and add to string
    doc.close() #close the PDF document
    return text #return the extracted text

def get_db_connection():
    return psycopg2.connect(
        #TODO: PLEASE REMOVE BUT THIS IS JUST FOR COPYING AND PASTING:
        #$env:DB='citvexdb';$env:DB_UN='citvex';$env:DB_PW='vexrobotics';
        host="drhscit.org",
        database=os.environ['DB'],
        user=os.environ['DB_UN'],
        password=os.environ['DB_PW']
    )

def reset():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute(
        "DROP TABLE IF EXISTS registry;" #remove the existing registry
        "CREATE TABLE registry (" #make a new one
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY," #id of the pdf, may not need this since the name could act as a primary key
            "name VARCHAR(255) UNIQUE NOT NULL," #unique name for the pdf
            "pdf_path TEXT NOT NULL," #path to the pdf file
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP" #timestamp of when the pdf was added
        ");"
    )
    con.commit()
    cur.close()
    con.close()
    if os.path.exists(STORAGE): #remove the directory if it exists
        shutil.rmtree(STORAGE)
    os.makedirs(os.path.join(STORAGE, "pdf"), exist_ok=True) #create the directory for storing pdfs
    os.makedirs(os.path.join(STORAGE, "txt"), exist_ok=True) #create the directory for storing the AI's results

def get_pdfs():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT name, timestamp FROM registry ORDER BY timestamp DESC;") #get the names and times added for each of the pdfs
    pdfs = cur.fetchall()
    cur.close()
    con.close()
    return pdfs

def upload_pdfs(list):
    con = get_db_connection()
    cur = con.cursor()
    for file in list: #for each pdf to upload,
        name = secure_filename(f"{str(uuid.uuid4())[:4]}_{file.filename}") #generate a unique name
        path = os.path.join(f"{STORAGE}/pdf", name) #generate the path to save the pdf
        file.save(path) #save the pdf to the path
        cur.execute("INSERT INTO registry (name, pdf_path) VALUES (%s, %s)", (name, path)) #add the name and path to the registry
    con.commit()
    cur.close()
    con.close()

def delete_pdf(name):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT pdf_path FROM registry WHERE name = %s", (name,)) #get the path of the pdf to delete
    path = cur.fetchone()[0]
    os.remove(path) #remove the pdf from that path
    cur.execute("DELETE FROM registry WHERE name = %s", (name,)) #remove the pdf from the registry
    con.commit()
    cur.close()
    con.close()