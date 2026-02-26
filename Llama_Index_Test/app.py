import os
import psycopg2
from flask import Flask, render_template, request, url_for, redirect
from llama_index.llms.ollama import Ollama
from llama_index.readers.schema.base import Document
from llama_index import VectorStoreIndex
from llmsherpa.readers import LayoutPDFReader

app = Flask(__name__)

llm = Ollama(
    model="llama3.2:3b",
    request_timeout=120.0,
    # Manually set the context window to limit memory usage
    context_window=8000,
)

prompt = "output the following information for a VEX Robotics Judge to \
            assist in their grading of a student engineering journal. \
            1. Notebook summary \
            2. Completeness score (structural, not rubric score) \
            3. Section presence checklist \
            4. Flags for judges to review \
            output your response in a structured manner with appropriate headings \
            make sure to not be overly verbose and write in a way that is easy to understand"

def get_db_connection():
    conn = psycopg2.connect(
        host="drhscit.org",
        database=os.environ["DB"],
        user=os.environ["DB_UN"],
        password=os.environ["DB_PW"])
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notebooks")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", notebooks=data)

@app.route("/upload/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        file = request.files["upload"]
        name = request.form["name"]

        notebook_reader = LayoutPDFReader(llmsherpa_api_url)
        notebook = notebook_reader.read_pdf(file)
        notebook_index = VectorStoreIndex([])
        for chunk in notebook.chunks():
            notebook_index.insert(Document(text=chunk.to_context_text(), extra_info={}))
        query_engine = notebook_index.as_query_engine()

        response = query_engine.query(prompt)

        conn = get_db_connection()
        cur = conn.cursor()
        if file:
            cur.execute('INSERT INTO notebooks (notebook_name, output)'
                        'VALUES (%s, %s)',
                        (name, response))
        else:
                cur.execute("INSERT INTO notebooks (notebook_name)"
                            "VALUES (%s)",
                            (name,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route("/view/<int:id>", methods = ("GET", "POST"))
def view(id):
    #GET:
    if request.method == "GET":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM notebooks WHERE id = %s", (id,))
        data = cur.fetchone()
        cur.close()
        conn.close()

        return render_template("view.html", notebook = data)

    #POST:
    elif request.method == "POST":
        name = request.form["name"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE notebooks SET name = %s WHERE id = %s",
                    (name, id))

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)