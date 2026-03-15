import os, shutil, psycopg2
from werkzeug.utils import secure_filename

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings, PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.readers.file import PyMuPDFReader

STORAGE = os.path.join(os.getcwd(), "vexnotebooks") #storage path on the machine the script runs on
RUBRIC = '''
    ### Section 1: Engineering Design Process
    | Criteria | Expert (4-5 Points) | Proficient (2-3 Points) | Emerging (0-1 Points) |
    | :--- | :--- | :--- | :--- |
    | **Identify Problem / Design Goal(s)** | Clearly identifies the problem / design goal(s) in detail at the start of each design process cycle. This can include elements of game strategy, robot design, or programming, and should include a clear definition and justification of the design goal(s), criteria, and constraints. | Identifies the problem / design goal(s) at the start of each design cycle but is lacking details or justification. | Does not identify the problem/design goal(s) at the start of each design cycle. |
    | **Brainstorm Solutions** | Explores several different solutions with explanation. Citations are provided for ideas that came from outside sources such as online videos or other teams. | Explores few solutions. Citations provided for ideas that came from outside sources. | Does not explore different solutions or solutions are recorded with little explanation. |
    | **Select Best Solution** | Fully explains the "why" behind design decisions in each step of the design process for all significant aspects of a team's design. | Inconsistently explains the "why" behind design decisions. | Minimally explains the "why" behind design decisions. |
    | **Build and Program the Solution** | Records the steps the team took to build and program the solution. Includes enough detail that the reader can follow the logic used by the team to develop their robot design, as well as recreate the robot design from the documentation. | Records the key steps to build and program the solution but lacks sufficient detail for the reader to follow their process. | Does not record the key steps to build and program the solution. |
    | **Original Testing of Solutions** | Records all the steps to test the solution, including test results. Testing methodology is clearly explained, and the testing is done by the team. Original testing results are explained and conclusions are drawn from that data. | Records the key steps to test the solution. Testing methodology may be incomplete, or incomplete conclusions are recorded. | Does not record steps to test the solution. Testing or results are borrowed from another team's work. |
    | **Repeat Design Process** | Shows that the design process is repeated multiple times to work towards a design goal. This includes a clear definition and justification of the design goal(s), its criteria, and constraints. The notebook shows setbacks that the team learned from, and shows design alternatives that were considered but not pursued. | Design process is not often repeated for design goals or robot/game performance. The notebook does not show alternate lines of inquiry, setbacks, or other learning experiences. | Does not show that the design process is repeated. Does not show setbacks or failures, or seems to be curated to craft a narrative. |

    ### Section 2: Format and Content
    | Criteria | Expert (4-5 Points) | Proficient (2-3 Points) | Emerging (0-1 Points) |
    | :--- | :--- | :--- | :--- |
    | **Independent Inquiry** | Team shows evidence of independent inquiry from the beginning stages of their design process. Notebook documents whether the implemented ideas have their origin with students on the team, or if students found inspiration elsewhere. | Team shows evidence of independent inquiry for some elements of their design process. Ideas and information from outside the team are documented. | Team shows little to no evidence of independent inquiry in their design process. Ideas from outside the team are not properly credited. Ideas or designs appear with no evidence of process. |
    | **Usability & Completeness** | Records the entire design and development process with enough clarity and detail that the reader could recreate the project's history. Notebook has recent entries that align with the robot the team has brought to the event. | Records the design and development process completely but lacks sufficient detail. Documentation is inconsistent with possible gaps. | Lacks sufficient detail to understand the design process. Notebook has large gaps in time, or does not align with the robot the team has brought to the event. |
    | **Originality & Quality** | Content is relevant and all content not original to the team longer than a paragraph is in appendices. Information originating from outside the team is always properly cited with the source and date accessed. Most or all content is original to the submitting team members. | Content is mostly relevant. Information originating from outside the team is properly credited. Cited content is paraphrased with some original content describing the team's design process. | Non-original content is excessive, is not kept in appendices, and/or is not cited. Plagiarised content should be noted to the JA pursuant to the RECF Code of Conduct process. |
    | **Organization / Readability** | Entries are logged in a table of contents. There is an overall organization (color coded entries, tabs, markers) that makes it easy to reference. Contains little to no extraneous content that does not further the engineering design process. | Entries are logged in a table of contents. There is some organization to enhance readability. Contains some extraneous content, but it does not severely impact readability. | Entries are not logged in a table of contents, and there is little adherence to organization. Excessive extraneous content makes the notebook difficult to read, use, or understand. |
    | **Record of Team & Project Management** | Provides a complete record of team and project assignments; contains team meeting notes including goals, decisions, and building/programming accomplishments; design cycles are easily identified. Resource constraints (time/materials) are noted throughout. Evidence documentation was done in sequence. Includes dates and names of contributing students. | Records most information but level of detail is inconsistent, or some aspects are missing. There are significant gaps in the overall record. Notebook may have inconsistent evidence of dates of entries and student contributions. | There are significant gaps or missing information for key design aspects. Notebook has little evidence of dates of entries and student contributions. |
'''

#reminder to pull both models `ollama pull [ model ]`
Settings.llm = Ollama(
    model="qwen2.5:14b",
    request_timeout=600,
    additional_kwargs={
        "temperature": 0.1
    }
)
Settings.embed_model = OllamaEmbedding(
    model_name="nomic-embed-text",
) 

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
    parser = SimpleNodeParser.from_defaults(chunk_size=512, chunk_overlap=20)
    for file in list: #for each pdf to upload,
        cur.execute("INSERT INTO registry (name) VALUES (%s) RETURNING id", (file.filename,)) #add the name to the registry to generate an id
        id = cur.fetchone()[0]

        fname = os.path.splitext(secure_filename(f"{id}{file.filename}"))[0] #generate a unique name
        
        pdf_path = os.path.join(f"{STORAGE}/pdf", f"{fname}.pdf") #generate the path to save the pdf
        idx_path = os.path.join(f"{STORAGE}/idx", fname) #generate the path to save the index
        res_path = os.path.join(f"{STORAGE}/res", f"{fname}.md") #generate the path to save the results

        file.save(pdf_path) #save the pdf to the path
        
        os.makedirs(idx_path, exist_ok=True) #make the directory for the index
        idx = VectorStoreIndex(parser.get_nodes_from_documents(reader.load_data(pdf_path))) #create the index from the pdf TODO: in the future use 1 idx for all notebooks
        idx.storage_context.persist(persist_dir=idx_path) #save the index to the path
        
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
    return RetrieverQueryEngine.from_args(
        get_idx(id).as_retriever(similarity_top_k=80),
        response_mode="tree_summarize",
        streaming=True,
        text_qa_template=PromptTemplate("""
            ### ROLE
            You are an expert **VEX Robotics Engineering Notebook judge** evaluating a team's engineering notebook according to the official judging rubric.
            Your job is to analyze the notebook content **objectively and evidence-first**, similar to a competition judge reviewing a submitted engineering notebook.
            ---
            ### CRITICAL SOURCE CITATION RULE
            You **MUST cite the notebook as your source for every claim**.
            All conclusions must reference **specific evidence from the notebook** such as:
            * quoted text
            * page references
            * section titles
            * timestamps or entry headings
            Use this citation format:
            `[Notebook Evidence: "<short quote or reference>"]`
            If evidence cannot be found, explicitly state:
            `[No clear evidence found in notebook]`
            **Never invent content or assume sections exist without evidence.**
            ---
            ### CONTEXT FROM NOTEBOOK
            {context_str}
            ---
            ### ENGINEERING NOTEBOOK RUBRIC REFERENCE
            {RUBRIC}
            ---
            ### EVALUATION REQUIREMENTS
            Your response must satisfy the following requirements.
            ---
            ## 1. Notebook Summary
            Provide a **concise summary of the team's project** including:
            * robot objective or challenge
            * key design direction
            * main technical approach
            * notable development milestones
            Each statement must reference notebook evidence.
            ---
            ## 2. Section Presence & Structural Completeness Audit
            Evaluate whether the following sections exist and are sufficiently documented:
            * Problem Definition & Goals
            * Brainstorming / Concept Generation
            * Design Decisions & Justification
            * Iteration / Redesign Documentation
            * Build & Programming Documentation
            * Testing & Results
            For each section provide:
            * **Status**: Present / Weak / Missing
            * **Evidence** (quote or reference)
            * **Notes on completeness**
            Then produce:
            **Structural Completeness Score (0–100)**
            Score reflects **presence of core engineering documentation sections**, not judging quality.
            Also output a **Section Presence Checklist**:
            | Section | Present | Weak | Missing | Evidence |
            | ------- | ------- | ---- | ------- | -------- |
            ---
            ## 3. Iteration Analysis
            Identify and count **documented iteration cycles or improvements**.
            An iteration counts if the notebook shows:
            * a problem or limitation
            * a modification or redesign
            * resulting outcome or reasoning
            Provide:
            * **Total iteration cycles detected**
            * A short bullet list of each iteration with cited evidence.
            ---
            ## 4. Authenticity & AI-Generated Content Check
            Analyze the notebook for indicators of:
            * AI-generated content
            * overly polished or non-student writing
            * missing trial-and-error documentation
            * lack of natural engineering process
            Flag potential concerns and explain **why**, supported by notebook evidence.
            Indicators may include:
            * sudden shifts in writing style
            * extremely formal or generic explanations
            * lack of mistakes, revisions, or iterative reasoning
            * vague summaries instead of engineering logs
            Provide:
            * **Risk level**: Low / Moderate / High
            * **Supporting evidence**
            ---
            ## 5. Rubric Comparison
            Compare the notebook against **each major rubric category**.
            For each category produce:
            ### Rubric Category: <Name>
            **Evidence Found**
            * Short excerpts or references
            * Each item must include notebook citations
            **Evidence Missing or Unclear**
            * Specific gaps relative to rubric expectations
            **Confidence Level**
            * High (clear strong evidence)
            * Medium (some evidence but incomplete)
            * Low (little or no evidence)
            **Suggested Judge Interview Questions**
            Provide **1–2 targeted questions** judges could ask the team to verify engineering understanding.
            ---
            ### OUTPUT FORMAT
            Structure your response exactly using these headings:
            1. Notebook Summary
            2. Section Presence & Structural Completeness
            3. Iteration Analysis
            4. Authenticity Check
            5. Rubric Comparison
            All sections must include **explicit notebook evidence citations**.
            ---
            ### USER QUERY
            {query_str}
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

    print('starting, now resetting')
    reset()
    print('resetted, now uploading')
    upload_pdfs(LFW(path) for path in [r"C:\Users\lawre\Downloads\Sample2-Engineering-notebook.pdf"])
    print('uploaded, now querying')
    res = query(get_pdfs()[0][0], "Perform a full judge evaluation of this notebook.")
    print('queried, now printing')
    for text in res.response_gen: 
        print(text, end="", flush=True)
