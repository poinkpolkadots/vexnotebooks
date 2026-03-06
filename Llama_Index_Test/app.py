# import os
# import psycopg2
# from flask import Flask, render_template, request, url_for, redirect
from llama_index.llms.ollama import Ollama
# from llama_index.core import Document
# from llama_index.core import VectorStoreIndex
# from llmsherpa.readers import LayoutPDFReader


# following code from this medium article, needs to be edited to directly output as text
# not as a chat engine
from flask import Flask, render_template, request
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
from llama_index import SimpleDirectoryReader
import pypdf
import os

app = Flask(__name__)

llama = Ollama(
    model="llama3.2:3b",
    request_timeout=120.0,
    # Manually set the context window to limit memory usage
    context_window=8000,
)

def read_data():
  reader = SimpleDirectoryReader(input_dir="data", recursive=True)
  docs = reader.load_data()

  service_context = ServiceContext.from_defaults(llm=llama)
  index = VectorStoreIndex.from_documents(docs, service_context=service_context)
  chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)
  return chat_engine

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf_file' in request.files:
        pdf_file = request.files['pdf_file']
        if pdf_file.filename.endswith('.pdf'):

            upload_folder = 'data'
            os.makedirs(upload_folder, exist_ok=True)
            pdf_path = os.path.join(upload_folder, pdf_file.filename)
            pdf_file.save(pdf_path)
            print(f"Uploaded PDF path: {pdf_path}")

            return render_template('view.html', upload_success=True)
        else:
            return render_template('index.html', upload_error="Invalid file format. Please upload a PDF.")
    else:
        return render_template('index.html', upload_error="No file uploaded.")

@app.route('/chat', methods=['POST'])
def chat():
    chat_engine = read_data()
    if request.method == 'POST':
        prompt = request.form['prompt']
        response = chat_engine.chat(prompt)
        return render_template('chat.html', prompt=prompt, response=response.response)

#
# llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
#
# prompt = "output the following information for a VEX Robotics Judge to \
#             assist in their grading of a student engineering journal. \
#             1. Notebook summary \
#             2. Completeness score (structural, not rubric score) \
#             3. Section presence checklist \
#             4. Flags for judges to review \
#             output your response in a structured manner with appropriate headings \
#             make sure to not be overly verbose and write in a way that is easy to understand"
#
# def get_db_connection():
#     conn = psycopg2.connect(
#         host="drhscit.org",
#         database=os.environ["DB"],
#         user=os.environ["DB_UN"],
#         password=os.environ["DB_PW"])
#     return conn
#
# @app.route("/")
# def index():
#     conn = get_db_connection()
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM notebooks")
#     data = cur.fetchall()
#     cur.close()
#     conn.close()
#     return render_template("index.html", notebooks=data)
#
# @app.route("/upload/", methods=("GET", "POST"))
# def upload():
#     if request.method == "POST":
#         name = request.form["name"]
#         file = request.files["upload"]
#         file_content = file.read().decode()
#
#         notebook_reader = LayoutPDFReader(llmsherpa_api_url)
#         notebook = notebook_reader.read_pdf(file_content)
#         notebook_index = VectorStoreIndex([])
#         for chunk in notebook.chunks():
#             notebook_index.insert(Document(text=chunk.to_context_text(), extra_info={}))
#         query_engine = notebook_index.as_query_engine()
#
#         response = query_engine.query(prompt)
#
#         conn = get_db_connection()
#         cur = conn.cursor()
#         if file:
#             cur.execute('INSERT INTO notebooks (notebook_name, output)'
#                         'VALUES (%s, %s)',
#                         (name, response))
#         else:
#                 cur.execute("INSERT INTO notebooks (notebook_name)"
#                             "VALUES (%s)",
#                             (name,))
#         conn.commit()
#         cur.close()
#         conn.close()
#         return redirect(url_for("index"))
#
#     return render_template("upload.html")
#
# @app.route("/view/<int:id>", methods = ("GET", "POST"))
# def view(id):
#     #GET:
#     if request.method == "GET":
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM notebooks WHERE id = %s", (id,))
#         data = cur.fetchone()
#         cur.close()
#         conn.close()
#
#         return render_template("view.html", notebook = data)
#
#     #POST:
#     elif request.method == "POST":
#         name = request.form["name"]
#
#         conn = get_db_connection()
#         cur = conn.cursor()
#         cur.execute("UPDATE notebooks SET name = %s WHERE id = %s",
#                     (name, id))
#
#         conn.commit()
#         cur.close()
#         conn.close()
#         return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)