import os
import psycopg2
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)

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

        conn = get_db_connection()
        cur = conn.cursor()
        if file:
            cur.execute('INSERT INTO notebooks (pdf, mimetype, name)'
                        'VALUES (%s, %s, %s, %s)',
                        (file.read(), file.mimetype, name))
        else:
                cur.execute("INSERT INTO notebooks (name)"
                            "VALUES (%s)",
                            (name,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route("/delete/<int:id>/")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notebooks WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))

@app.route("/view/<int:id>", methods = ("GET", "POST"))
def edit(id):
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