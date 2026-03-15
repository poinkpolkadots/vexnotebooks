import os, shutil, psycopg2
from werkzeug.utils import secure_filename
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings, PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.readers.file import PyMuPDFReader

#os.environ["LLAMA_CLOUD_API_KEY"] = "llx-2Ejopk7UhAlQFzhvvCKy4zh3yxs7qbqiEl2yVXzFxu9ZcnbF"

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on

#reminder to pull both models `ollama pull [ model ]`
Settings.llm = Ollama(
    model="qwen2.5:32b",
    request_timeout=600,
    context_window=32768,
    additional_kwargs={
        "num_ctx": 32768,
        "temperature": 0.1
    }
)
Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    additional_kwargs={"num_ctx" : 8192}
) 
Settings.chunk_size = 1200
Settings.chunk_overlap = 150

splitter = MarkdownNodeParser()

def get_db_connection():
    return psycopg2.connect(
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

def get_pdfs():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id, name, timestamp FROM registry ORDER BY timestamp DESC;") #get the names and times added for each of the pdfs
    pdfs = cur.fetchall()
    cur.close()
    con.close()
    return pdfs

def upload_pdfs(list):
    con = get_db_connection()
    cur = con.cursor()
    reader = PyMuPDFReader()
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[4096, 1024])
    for file in list: #for each pdf to upload,
        cur.execute("INSERT INTO registry (name) VALUES (%s) RETURNING id", (file.filename,)) #add the name to the registry to generate an id
        id = cur.fetchone()[0]
        fname = secure_filename(f"{id}{file.filename}") #generate a unique name
        pdf_path = os.path.join(f"{STORAGE}/pdf", fname) #generate the path to save the pdf
        file.save(pdf_path) #save the pdf to the path
        idx_path = os.path.join(f"{STORAGE}/idx", fname) #generate the path to save the index
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        documents = documents = reader.load_data(pdf_path)
        for d in documents:
            d.metadata["notebook"] = fname
        nodes = node_parser.get_nodes_from_documents(documents)
        for node in nodes:
            node.metadata["notebook"] = fname
        idx = VectorStoreIndex(nodes) #create the index from the pdf
        idx.storage_context.persist(persist_dir=idx_path) #save the index to the path
        res_path = os.path.join(f"{STORAGE}/res", f"{fname}.md") #generate the path to save the results
        with open(res_path, "w") as f: #create an empty file for the results
            f.write("")
        cur.execute("UPDATE registry SET pdf_path = %s, idx_path = %s, res_path = %s WHERE id = %s", (pdf_path, idx_path, res_path, id)) #add the name and paths to the registry
    con.commit()
    cur.close()
    con.close()

def delete_pdf(id):
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

def get_idx(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT idx_path FROM registry WHERE id = %s", (id,)) #get the path of the index to load
    idx_path = cur.fetchone()[0]
    cur.close()
    con.close()
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=idx_path)) #load the index from that path and return it

def query(id, query):
    idx = get_idx(id)
    return RetrieverQueryEngine.from_args(
        RecursiveRetriever( #this may be the bottleneck?
            "vector",
            retriever_dict={"vector" : idx.as_retriever(similarity_top_k=20)}, #originally 80
            node_dict={node.node_id: node for node in list(idx.docstore.docs.values())},
            verbose=True
        ),
        response_mode="compact",
        streaming=True,
        text_qa_template=PromptTemplate("""
            You are a VEX Robotics Engineering Notebook judge evaluating Team 97265A (Jagbots).

            Question:
            {query_str}

            Analyze the notebook and extract evidence describing the team's engineering process.

            Focus especially on:

            • Brainstorming ideas and rejected concepts
            • Design decisions and why designs were selected
            • Mechanical subsystems (intake, drivetrain, etc.)
            • Testing results and experiments
            • Meeting discussions and engineering decisions
            • Chronological development of the robot

            Rules:
            - Cite notebook pages like [Page X]
            - Quote important engineering notes when helpful
            - Reproduce tables if test data appears
            - Reconstruct the timeline of development when possible

            Context:
            {context_str}

            Engineering Analysis:
        """)
    ).query(query)

def set_res(id, res):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT res_path FROM registry WHERE id = %s", (id,)) #get the path of the results file to save to
    path = cur.fetchone()[0]
    with open(path, "w") as f: #save the results to that path
        f.write(res)
    cur.close()
    con.close()

def get_res(id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT res_path FROM registry WHERE id = %s", (id,)) #get the path of the results file to read from
    path = cur.fetchone()[0]
    with open(path, "r") as f: #read the results from that path and return them
        res = f.read()
    cur.close()
    con.close()
    return res

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

    #print('starting, now resetting')
    #reset()
    #print('resetted, now uploading')
    #upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    print('uploaded, now querying')
    res = query(get_pdfs()[0][0], "what did Maxwell contribute to the team's engineering process?")
    print('queried, now printing')
    for text in res.response_gen: 
        print(text, end="", flush=True)
