import os, shutil, psycopg2, yaml, json, fitz, io
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from enum import Enum

from llama_index.core import VectorStoreIndex, StorageContext, PromptTemplate, SimpleDirectoryReader, load_index_from_storage, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine

load_dotenv() #for testing, load envs from .env file

STORAGE = "/app/storage" #storage using docker
#STORAGE = os.path.join(os.getcwd(), "storage") #testing storage
PROMPTS = yaml.safe_load(open('prompts.yaml', 'r', encoding='utf-8')) #all the prompts used

class Task(Enum): #each task prompt, enum used for static typing
    SUMMARY = PROMPTS['tasks']['summary']
    SECTIONS = PROMPTS['tasks']['sections']
    ITERATION = PROMPTS['tasks']['iteration']
    FLAGS = PROMPTS['tasks']['flags']
    RUBRIC = PROMPTS['tasks']['rubric']

class LFW: #NOTE only for testing purposes (local file wrapper thingy)
    def __init__(self, local_path):
        self.local_path = local_path
        self.filename = os.path.basename(local_path)
    def save(self, destination):
        shutil.copyfile(self.local_path, destination)

#reminder to pull both models `ollama pull [ model ]`
Settings.llm = Ollama(
    model="qwen2.5:7b",
    base_url="http://ollama:11434",
    request_timeout=3600,
    additional_kwargs={
        "temperature": 0.1,
        "num_ctx": 32768
    })

Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://ollama:11434")

def get_db_connection() -> psycopg2.extensions.connection: #get a connection from the database
    return psycopg2.connect(
        host=os.getenv('HOST', 'db'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB'), 
        user=os.getenv('DB_UN'),
        password=os.getenv('DB_PW'))

def reset() -> None: #reset the db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DROP TABLE IF EXISTS registry;" #remove the existing registry
        "CREATE TABLE registry (" #make a new one
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY," #id of the pdf
            "name VARCHAR(255) NOT NULL," #name for the pdf
            "dir TEXT," #path to the directory
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP," #timestamp of when the pdf was added
            "status TEXT CHECK(status = 'pending' OR status = 'processing' OR status = 'complete') DEFAULT 'pending'" #if the llm has generated responses yet
        ");")
    conn.commit()
    cur.close()
    conn.close()
    if os.path.exists(STORAGE): shutil.rmtree(STORAGE) #remove the directory if it exists
    os.makedirs(os.path.join(STORAGE, "notebooks"), exist_ok=True) #make directory for pdfs

def get_pdfs() -> tuple: #get all pdfs from db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, timestamp FROM registry ORDER BY timestamp DESC;")
    pdfs = cur.fetchall() #get the ids, names, and times added for each of the pdfs
    cur.close()
    conn.close()
    return pdfs

def upload_pdfs(list: list) -> None: #upload a list of pdfs
    uploaded_ids = [] # list of all ids of uploaded pdfs
    conn = get_db_connection()
    cur = conn.cursor()
    for file in list: #for each pdf to upload,
        cur.execute("INSERT INTO registry (name) VALUES (%s) RETURNING id", (file.filename,))
        id = cur.fetchone()[0] #add the name to the registry to generate an id
        uploaded_ids.append(id)
        fname = os.path.splitext(secure_filename(f"{id}{file.filename}"))[0] #generate a unique name
        dir = os.path.join(STORAGE, "notebooks", fname) #create the name for the directory
        os.makedirs(dir, exist_ok=True) #actually make the directory
        pdf_path = os.path.join(dir, "source.pdf") #generate the path to save the pdf
        idx_path = os.path.join(dir, "idx") #generate the path to save the index
        res_path = os.path.join(dir, "res.json") #generate the path to save the results
        file.save(pdf_path) #save the pdf to the path
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        idx = VectorStoreIndex.from_documents(SimpleDirectoryReader(input_files=[pdf_path]).load_data()) #create the index from the pdf
        idx.storage_context.persist(persist_dir=idx_path) #save the index to the path
        with open(res_path, 'w') as f: json.dump({}, f) #initialize the json as empty
        cur.execute("UPDATE registry SET dir = %s WHERE id = %s", (dir, id)) #add the name and paths to the registry
    conn.commit()
    cur.close()
    conn.close()
    return uploaded_ids # return all the ids of the uploaded pdfs

def get_pdf(id: int) -> str: #gets the absolute path of a pdf
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT dir FROM registry WHERE id = %s;", (id,))
    dir = cur.fetchone()[0] #gets the directory of the pdf
    cur.close()
    conn.close()
    return os.path.abspath(os.path.join(dir, "source.pdf")) #returns the path of the source pdf

def get_pdf_thumb(id: int) -> io.BytesIO: #turns the first page of the pdf into a image
    with fitz.open(get_pdf(id)) as doc: #opens the pdf
        return io.BytesIO(doc.load_page(0).get_pixmap(alpha=False).tobytes("png")) #gets the first page and returns a .png of it

def delete_pdf(id: int) -> None: #delete a pdf
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM registry WHERE id = %s RETURNING dir", (id,)) #remove the pdf from the registry
    dir = cur.fetchone()[0] #get the paths to the pdf, index, and results file
    if os.path.exists(dir): shutil.rmtree(dir) #remove the directory
    conn.commit()
    cur.close()
    conn.close()

def get_idx(id: int) -> VectorStoreIndex: #get an idx
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT dir FROM registry WHERE id = %s", (id,))
    idx_path = os.path.join(cur.fetchone()[0], "idx") #get the path of the index to load
    cur.close()
    conn.close()
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=idx_path)) #load the index from that path and return it

def set_res(id: int, task: Task, res: str) -> None: #set a result
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT dir FROM registry WHERE id = %s", (id,))
    res_path = os.path.join(cur.fetchone()[0], "res.json") #get the path of the results file to save to
    cur.close()
    conn.close()
    with open(res_path, 'r') as f: data = json.load(f) #get the current state
    data[task.name.lower()] = res #update the specific task to have the new result
    with open(res_path, 'w') as f: json.dump(data, f) #save the updated state

def get_res(id: int, task: Task = None) -> str: #get a result
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT dir FROM registry WHERE id = %s", (id,))
    res_path = os.path.join(cur.fetchone()[0], "res.json") #get the path of the results file to read from
    cur.close()
    conn.close()
    with open(res_path, 'r', encoding='utf-8') as f: data = json.load(f) #get the current state
    return data.get(task.name.lower()) if task else data #return value for the key of the task, if no task specified return the whole thing

def query(idx: VectorStoreIndex, task: Task) -> str: #query the llm to do a task
    return RetrieverQueryEngine.from_args(
        idx.as_retriever(similarity_top_k=30), #get chunks from the pdf
        response_mode="compact",
        text_qa_template=PromptTemplate(PROMPTS['base'].format( #use the prompt that includes the rubric, context from pdf, and the task
            rubric_ref = PROMPTS['rubric_ref'],
            context_str = "{context_str}",
            query_str="{query_str}"
    ))).query(task.value).response #enter the task as the query

def query_and_write_all(id : int): #does all the tasks for a pdf
    print(f'loading idx')
    idx = get_idx(id)
    for t in Task:
        print(f'starting {t.name}')
        set_res(id, t, query(idx, t))
        print(f'finished {t.name}')

if __name__ == "__main__": #NOTE only for testing!!
    con = get_db_connection()
    #reset()
    #upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    #query_and_write_all(get_pdfs()[0][0])