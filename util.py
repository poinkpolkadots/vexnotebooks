import os, shutil, psycopg2, uuid
from werkzeug.utils import secure_filename
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings, PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import LLMRerank

os.environ["LLAMA_CLOUD_API_KEY"] = "llx-2Ejopk7UhAlQFzhvvCKy4zh3yxs7qbqiEl2yVXzFxu9ZcnbF"

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on

#reminder to pull both models `ollama pull [ model ]`
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
Settings.chunk_size = 512
Settings.chunk_overlap = 50

splitter = MarkdownNodeParser()

class LFW:
    def __init__(self, local_path):
        self.local_path = local_path
        self.filename = os.path.basename(local_path)
    def save(self, destination):
        shutil.copyfile(self.local_path, destination)

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

    parser = LlamaParse(
        result_type="markdown",
        user_prompt=(
            "This is a VEX Robotics Engineering Notebook."
            "Focus on capturing:"
            "- Hand-written dates and page numbers (usually at the top or bottom corner)."
            "- Pros/Cons tables and comparison charts."
            "- Test logs and data tables."
            "- Captions under drawings/images describing robot subsystems."
        ),
        parsing_instruction=(
            "This is a high-stakes VEX Robotics Engineering Notebook. "
            "Every handwritten note, page number, and date is critical. "
            "If you see a table, reconstruct it perfectly in Markdown. "
            "If you see a drawing, describe it in detail as text."
        )
    )
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 1024, 512])

    for file in list: #for each pdf to upload,
        name = secure_filename(f"{str(uuid.uuid4())[:4]}_{file.filename}") #generate a unique name
        pdf_path = os.path.join(f"{STORAGE}/pdf", name) #generate the path to save the pdf
        file.save(pdf_path) #save the pdf to the path
        idx_path = os.path.join(f"{STORAGE}/idx", name) #generate the path to save the index
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        
        documents = SimpleDirectoryReader(input_files=[pdf_path], file_extractor={".pdf": parser}).load_data()
        nodes = node_parser.get_nodes_from_documents(documents)

        idx = VectorStoreIndex(nodes) #create the index from the pdf
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
    all_nodes = list(idx.docstore.docs.values())

    retriever = RecursiveRetriever(
        "vector",
        retriever_dict={"vector":idx.as_retriever(similarity_top_k=60)},
        node_dict={node.node_id:node for node in all_nodes},
        verbose=True
    )

    rank = LLMRerank(top_n=20, model="llama3.2")

    engine = RetrieverQueryEngine.from_args(
        retriever,
        streaming=True,
        node_postprocessors=[rank],
        response_mode="tree_summarize",
        text_qa_template=PromptTemplate(
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "You are an expert VEX Robotics Judge. Your task is to provide an EXTREMELY DETAILED "
            "technical audit of the team's engineering process based ONLY on the context provided.\n\n"
            
            "RULES:\n"
            "1. LIST EVERY design option mentioned (e.g., Ball Bag, Elevator, Magazine, etc.).\n"
            "2. For every design, list the specific PROS and CONS mentioned in the text.\n"
            "3. Describe every TEST conducted, including the DATE and the RESULT (e.g., 6/10 rings success).\n"
            "4. Identify every FAILURE or ISSUE and describe the exact SOLUTION the team implemented.\n"
            "5. YOU MUST CITE THE PAGE NUMBER for every single fact you provide (e.g., [Page 12]).\n"
            "6. Use bullet points for readability but do not sacrifice detail.\n\n"

            "### INSTRUCTIONS FOR TECHNICAL AUDIT:\n"
            "1. EXTRACT ALL DATES: Scan the context for every date mentioned.\n"
            "2. TRACK EVOLUTION: Look for phrases like 'Instead of', 'We changed', or 'Version 2'.\n"
            "3. DATA RECOVERY: If you find a test result (e.g., 5/5 or 60%), you MUST include it.\n"
            "4. NO SUMMARIES: Do not say 'The team tested the robot.' Say 'On 12/23, the team "
            "tested the intake and achieved a 6/10 success rate due to entrance clogging.'\n"
            "5. SOURCE EVERYTHING: Every bullet point MUST end with [Page X].\n"

            "Query: {query_str}\n"
            "Judge's Detailed Technical Assessment:"
        )
    )
    return engine.query(query)

if __name__ == "__main__":
    os.environ['DB'] = 'citvexdb'
    os.environ['DB_UN'] = 'citvex'
    os.environ['DB_PW'] = 'vexrobotics'

    print('starting, now resetting')
    reset()
    print('resetted, now uploading')
    upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    print('uploaded, now querying')
    res = query(get_pdfs()[0][0], "tell me their development process for the intake")
    print('queried, now printing')
    for text in res.response_gen: 
        print(text, end="", flush=True)