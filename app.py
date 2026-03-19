import secrets
from flask import Flask, render_template, request, redirect, url_for
from util import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/catalog/')
def catalog():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM registry")
    data = cur.fetchall()
    return render_template('catalog.html', notebooks = data)

@app.route('/notebookinfo/<int:id>')
def notebookinfo(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM registry WHERE id = %s" (id,))
    data = cur.fetchone()

    return render_template('notebookinfo.html', name = data, output = get_res(id))

@app.route('/upload/', methods=("GET", "POST"))
def upload():
    if request.method == "GET":
        return render_template('upload.html')
    elif request.method == "POST":
        pdfs = request.files["files"]
        ids = upload_pdfs(pdfs)
        for id in ids:
            query_and_write_all(id)
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)