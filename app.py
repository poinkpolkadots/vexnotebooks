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
    return render_template('catalog.html', notebooks = get_pdfs())

@app.route('/notebookinfo/<int:id>')
def notebookinfo(id):
    return render_template('notebookinfo.html', output = get_res(id))

@app.route('/pdfthumb/<int:id>')
def pdfthumb(id):
    return send_file(get_pdf_thumb(id), 'image/png')

@app.route('/upload/', methods=("GET", "POST"))
def upload():
    if request.method == "GET":
        return render_template('upload.html')
    elif request.method == "POST":
        pdfs = request.files.getlist("files")
        upload_pdfs(pdfs)
        return redirect(url_for("catalog"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)