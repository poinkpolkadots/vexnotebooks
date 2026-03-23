import secrets
from flask import *
from util import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/catalog/')
def catalog():
    return render_template('catalog.html', notebooks = get_pdfs()) # pass all uploaded PDFs to catalog template

@app.route('/notebookinfo/<int:id>')
def notebookinfo(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM registry WHERE id = %s", (id,)) # get the name of the notebook from the registry so that everything looks nice
    data = cur.fetchone()
    return render_template('notebookinfo.html', name = data, output = {k: format_markdown(v) for k, v in get_res(id).items()}) # pass the notebook name, and the response, formatted as markdown

@app.route('/pdfthumb/<int:id>')
def pdfthumb(id):
    return send_file(get_pdf_thumb(id), 'image/png') # make the PDF thumbnail for catalog viewing

@app.route('/upload/', methods=("GET", "POST"))
def upload():
    if request.method == "GET":
        return render_template('upload.html') # render the upload template
    elif request.method == "POST":
        pdfs = request.files.getlist("files") # get all the uploaded files
        upload_pdfs(pdfs)
        return redirect(url_for("catalog"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)