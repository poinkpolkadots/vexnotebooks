import os, shutil, psycopg2, uuid
from werkzeug.utils import secure_filename
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings, PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on

#reminder to pull both models `ollama pull llama3.2` and `ollama pull nomic-embed-text`
Settings.llm = Ollama(
    model="llama3.2", 
    request_timeout=300.0, 
    context_window=32768,
    additional_kwargs={"num_ctx" : 32768}
)
Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    additional_kwargs={"num_ctx" : 8192}
)
Settings.chunk_size = 8192
Settings.chunk_overlap = 4096

class LFW:
    def __init__(self, local_path):
        self.local_path = local_path
        self.filename = os.path.basename(local_path)
    def save(self, destination):
        shutil.copyfile(self.local_path, destination)

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
            "idx_path TEXT NOT NULL," #path to the index file
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP" #timestamp of when the pdf was added
        ");"
    )
    con.commit()
    cur.close()
    con.close()
    if os.path.exists(STORAGE): #remove the directory if it exists
        shutil.rmtree(STORAGE)
    os.makedirs(os.path.join(STORAGE, "pdf"), exist_ok=True) #create the directory for storing pdfs
    os.makedirs(os.path.join(STORAGE, "idx"), exist_ok=True) #create the directory for storing the AI's results

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
        pdf_path = os.path.join(f"{STORAGE}/pdf", name) #generate the path to save the pdf
        file.save(pdf_path) #save the pdf to the path
        idx_path = os.path.join(f"{STORAGE}/idx", name) #generate the path to save the index
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        idx = VectorStoreIndex.from_documents(SimpleDirectoryReader(input_files=[pdf_path]).load_data()) #create the index from the pdf
        idx.storage_context.persist(persist_dir=idx_path) #save the index to the path
        cur.execute("INSERT INTO registry (name, pdf_path, idx_path) VALUES (%s, %s, %s)", (name, pdf_path, idx_path)) #add the name and paths to the registry
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

def get_idx(name):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT idx_path FROM registry WHERE name = %s", (name,)) #get the path of the index to load
    IDX_PATH = cur.fetchone()[0]
    cur.close()
    con.close()
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=IDX_PATH)) #load the index from that path and return it

def query(name, query):
    idx = get_idx(name)
    qa = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, "
        "answer the query in a detailed, technical, and comprehensive manner. "
        "If the engineering notebook describes specific iterations, failures, or "
        "materials used, include those details. Always cite the page numbers found in the metadata.\n"
        "Query: {query_str}\n"
        "Answer: "
    )
    engine = idx.as_query_engine(
        simmilarity_top_k=5, 
        text_qa_template=qa
    )
    return engine.query(query)

if __name__ == "__main__":
    #reset()
    #upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    print(query(get_pdfs()[0][0], "what were the problems they had with intake and what were their solutions? please include the page number in your answer"))