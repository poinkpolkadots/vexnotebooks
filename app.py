import secrets, uuid
from werkzeug.utils import secure_filename
from init_db import *
from flask import *
from data import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
app.config["UPLOAD_FOLDER"] = pdf_folder

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, timestamp FROM registry ORDER BY timestamp DESC;")
    pdfs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", pdfs=pdfs)

@app.route("/upload", methods=("GET", "POST"))
def upload():
    if request.method == "POST":
        files = request.files.getlist("file")
        conn = get_db_connection()
        cur = conn.cursor()

        for file in files:
            name = secure_filename(f"{str(uuid.uuid4())[:4]}_{file.filename}")
            path = os.path.join(app.config["UPLOAD_FOLDER"], name)
            file.save(path)
            cur.execute("INSERT INTO registry (name, path) VALUES (%s, %s)", (name, path))
        
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/view/<name>")
def view(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

@app.route("/delete/<name>")
def delete(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT path FROM registry WHERE name = %s", (name,))
    path = cur.fetchone()[0]
    os.remove(path)
    cur.execute("DELETE FROM registry WHERE name = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)