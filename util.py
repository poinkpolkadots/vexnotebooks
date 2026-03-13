import os, shutil, psycopg2, uuid
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

    reader = PyMuPDFReader()

    #reader = DoclingReader()

    #parser = LlamaParse(
    #    result_type="markdown",
    #    auto_mode=True,
    #    user_prompt=(
    #        "This document is a VEX Robotics Engineering Notebook from team 97265A (Jagbots). "
    #        "It contains chronological engineering notes, meeting logs, and robot development."
    #    ),
    #    parsing_instruction=(
    #        "This is a structured engineering notebook used for robotics competition judging.\n\n"
    #
    #       "DOCUMENT STRUCTURE:\n"
    #        "- Pages contain dated engineering entries.\n"
    #        "- Many sections are TEAM MEETING NOTES.\n"
    #        "- Some pages contain brainstorming, design selection, testing, or code.\n\n"
    #
    #        "IMPORTANT EXTRACTION RULES:\n"
    #
    #        "1. Always preserve page numbers as headings like:\n"
    #        "   ### Page X\n\n"
    #
    #        "2. Preserve dates exactly as written (example: 9/1/25, 12/16/25).\n\n"
    #
    #        "3. Preserve section titles such as:\n"
    #        "- Brainstorming Solutions\n"
    #        "- Selecting Designs\n"
    #        "- Testing Solutions\n"
    #        "- Identify the Problem\n"
    #        "- Team Meeting Notes\n"
    #        "- Code\n\n"
    #
    #        "4. If you see a meeting log, extract it as bullet points.\n\n"
    #
    #        "5. If you see a test log or results, reconstruct it as a markdown table.\n\n"
    #
    #        "6. If the page contains robot mechanisms (intake, drivetrain, etc.), "
    #        "describe the design and components clearly.\n\n"
    #
    #        "7. DO NOT summarize. Preserve the engineering notes exactly."
    #    )
    #)
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[4096, 1024])

    for file in list: #for each pdf to upload,
        name = secure_filename(f"{str(uuid.uuid4())[:4]}_{file.filename}") #generate a unique name
        pdf_path = os.path.join(f"{STORAGE}/pdf", name) #generate the path to save the pdf
        file.save(pdf_path) #save the pdf to the path
        idx_path = os.path.join(f"{STORAGE}/idx", name) #generate the path to save the index
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        documents = documents = reader.load_data(pdf_path) #SimpleDirectoryReader(input_files=[pdf_path], file_extractor={".pdf": parser}).load_data()
        for d in documents:
            d.metadata["notebook"] = name
        nodes = node_parser.get_nodes_from_documents(documents)
        for node in nodes:
            node.metadata["notebook"] = name
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
    #retriever = AutoMergingRetriever(
    #    idx.as_retriever(similarity_top_k=80),
    #    idx.storage_context,
    #    verbose=True
    #)
    retriever = RecursiveRetriever(
        "vector",
        retriever_dict={"vector" : idx.as_retriever(similarity_top_k=80)},
        node_dict={node.node_id: node for node in list(idx.docstore.docs.values())},
        verbose=True
    )
    engine = RetrieverQueryEngine.from_args(
        retriever,
        #node_postprocessors=[LLMRerank(top_n=50)],
        response_mode="refine",
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
    res = query(get_pdfs()[0][0], "what did Maxwell contribute to the team's engineering process?")
    print('queried, now printing')
    for text in res.response_gen: 
        print(text, end="", flush=True)