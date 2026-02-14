import secrets
from init_db import get_db_connection
from flask import *
from data import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
app.config["UPLOAD_FOLDER"] = "C:\\vexpdfs"

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
        file = request.files["file"]
        if file:
            name = file.filename
            path = os.path.join(app.config["UPLOAD_FOLDER"], name)
            file.save(path)
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO registry (name, path) VALUES (%s, %s)", (name, path))
            conn.commit()
            cur.close()
            conn.close()
        return redirect(url_for("index"))
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)