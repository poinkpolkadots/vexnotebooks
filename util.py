import os, shutil, psycopg2, yaml, json
from werkzeug.utils import secure_filename
from enum import Enum

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings, PromptTemplate, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.query_engine import RetrieverQueryEngine

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on

def get_prompts():
    with open('prompts.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
PROMPTS = get_prompts()

class Task(Enum):
    SUMMARY = PROMPTS['tasks']['summary']
    SECTIONS = PROMPTS['tasks']['sections']
    ITERATION = PROMPTS['tasks']['iteration']
    FLAGS = PROMPTS['tasks']['flags']
    RUBRIC = PROMPTS['tasks']['rubric']

#reminder to pull both models `ollama pull [ model ]`
Settings.llm = Ollama(
    model="qwen2.5:7b",
    request_timeout=3600,
    additional_kwargs={
        "temperature": 0.1,
        "num_ctx": 32768
    }
)
Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
)

def get_db_connection(): #cant seem to find the `connection` return val but its ok
    return psycopg2.connect(
        #host="drhscit.org",
        #database=os.environ['DB'],
        #user=os.environ['DB_UN'],
        #password=os.environ['DB_PW']
        host="localhost",
        database="vexpdfs",
        user="postgres",
        password="1q2w3e4r"
    )

def reset() -> None:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute(
        "DROP TABLE IF EXISTS registry;" #remove the existing registry
        "CREATE TABLE registry (" #make a new one
            "id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY," #id of the pdf
            "name VARCHAR(255) NOT NULL," #name for the pdf
            "pdf_path TEXT," #path to the pdf file
            "idx_path TEXT," #path to the index file
            "res_path TEXT," #path to the results file
            "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP" #timestamp of when the pdf was added
        ");")
    con.commit()
    cur.close()
    con.close()
    if os.path.exists(STORAGE): #remove the directory if it exists
        shutil.rmtree(STORAGE)
    os.makedirs(os.path.join(STORAGE, "pdf"), exist_ok=True) #create the directory for storing pdfs
    os.makedirs(os.path.join(STORAGE, "idx"), exist_ok=True) #create the directory for storing the AI's vector stores
    os.makedirs(os.path.join(STORAGE, "res"), exist_ok=True) #create the directory for storing the AI's responses

def get_pdfs() -> tuple:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id, name, timestamp FROM registry ORDER BY timestamp DESC;") #get the names and times added for each of the pdfs
    pdfs = cur.fetchall()
    cur.close()
    con.close()
    return pdfs

def upload_pdfs(list: list) -> None:
    con = get_db_connection()
    cur = con.cursor()
    for file in list: #for each pdf to upload,
        cur.execute("INSERT INTO registry (name) VALUES (%s) RETURNING id", (file.filename,)) #add the name to the registry to generate an id
        id = cur.fetchone()[0]
        fname = os.path.splitext(secure_filename(f"{id}{file.filename}"))[0] #generate a unique name
        pdf_path = os.path.join(f"{STORAGE}/pdf", f"{fname}.pdf") #generate the path to save the pdf
        idx_path = os.path.join(f"{STORAGE}/idx", fname) #generate the path to save the index
        res_path = os.path.join(f"{STORAGE}/res", f"{fname}.json") #generate the path to save the results
        file.save(pdf_path) #save the pdf to the path
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        idx = VectorStoreIndex.from_documents(SimpleDirectoryReader(input_files=file).load_data()) #create the index from the pdf TODO: in the future use 1 idx for all notebooks
        idx.storage_context.persist(persist_dir=idx_path) #save the index to the path
        with open(res_path, 'w') as f:
            json.dump({}, f)
        cur.execute("UPDATE registry SET pdf_path = %s, idx_path = %s, res_path = %s WHERE id = %s", (pdf_path, idx_path, res_path, id)) #add the name and paths to the registry
    con.commit()
    cur.close()
    con.close()

def delete_pdf(id: int) -> None:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM registry WHERE id = %s RETURNING (pdf_path, idx_path, res_path)", (id,)) #remove the pdf from the registry
    pdf_path, idx_path, res_path = cur.fetchone() #get the paths to the pdf, index, and results file
    if os.path.exists(pdf_path): #remove the pdf file
        os.remove(pdf_path)
    if os.path.exists(idx_path): #remove the index directory
        shutil.rmtree(idx_path)
    if os.path.exists(res_path): #remove the results file
        os.remove(res_path)
    con.commit()
    cur.close()
    con.close()

def get_idx(id: int) -> VectorStoreIndex:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT idx_path FROM registry WHERE id = %s", (id,)) #get the path of the index to load
    idx_path = cur.fetchone()[0]
    cur.close()
    con.close()
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=idx_path)) #load the index from that path and return it

def query(id: int, task: Task) -> str:
    return RetrieverQueryEngine.from_args(
        get_idx(id).as_retriever(similarity_top_k=30),
        response_mode="compact",
        text_qa_template=PromptTemplate(PROMPTS['base'].format(
            rubric_ref = PROMPTS['rubric_ref'],
            context_str = "{context_str}",
            query_str="{query_str}"
        ))
    ).query(task.value).response

def set_res(id: int, task: Task, res: str) -> None:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT res_path FROM registry WHERE id = %s", (id,)) #get the path of the results file to save to
    res_path = cur.fetchone()[0]
    cur.close()
    con.close()
    with open(res_path, 'r') as f:
        data = json.load(f)
    data[task.name.lower()] = res
    with open(res_path, 'w') as f:
        json.dump(data, f)

def get_res(id: int, task: Task = None) -> str:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT res_path FROM registry WHERE id = %s", (id,)) #get the path of the results file to read from
    res_path = cur.fetchone()[0]
    cur.close()
    con.close()
    with open(res_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(task.name.lower()) if task else data

def query_and_write_all(id : int):
    for t in Task:
        set_res(id, t, query(id, t))
        print(f'finished {t.name}')

class LFW: #NOTE only for testing purposes (local file wrapper thingy)
    def __init__(self, local_path):
        self.local_path = local_path
        self.filename = os.path.basename(local_path)
    def save(self, destination):
        shutil.copyfile(self.local_path, destination)

if __name__ == "__main__":
    os.environ['DB'] = 'citvexdb'
    os.environ['DB_UN'] = 'citvex'
    os.environ['DB_PW'] = 'vexrobotics'

    reset()
    upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    query_and_write_all(get_pdfs()[0][0])