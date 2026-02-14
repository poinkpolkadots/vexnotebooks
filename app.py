import secrets
from init_db import get_db_connection
from flask import *
from data import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, date FROM main ORDER BY id DESC;")
    pdfs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", pdfs=pdfs)

if __name__ == "__main__":
    app.run(debug=True)