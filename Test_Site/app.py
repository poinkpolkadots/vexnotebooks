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
        file = request.files['upload']
        name = request.form["name"]

        conn = get_db_connection()
        cur = conn.cursor()
        if file:
                cur.execute('INSERT INTO notebooks (pdf, mimetype, name)'
                            'VALUES (%s, %s, %s)',
                            (file.read(),file.mimetype, name))    
        else:
                cur.execute('INSERT INTO notebooks (name)'
                            'VALUES (%s)',
                            (name,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route("/delete/<int:id>/")
def delete(id):
    #Your code here - what should happen when a user clicks "Delete Review" on a particular review (with the specified id)? 
    # runs a delete from statement where the id matches the inputted id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notebooks WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    #Note - no need to change the code below - this will redirect the user back to the reviews page once they"ve deleted a review.
    return redirect(url_for("index"))

@app.route("/edit/<int:id>", methods = ("GET", "POST"))
def edit(id):
    #GET:
    if request.method == "GET":
        #Your code here - what should happen when a user clicks "Edit Review" on a particular review (with the specified id)?
        #in the form, the value attribute should be set to the existing review fields
        #connect from database, select all where id matches
        #modify render template statement to pass in data from table
        #use fetchone() to get info and store in variable
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM notebooks WHERE id = %s", (id,))
        data = cur.fetchone()
        cur.close()
        conn.close()

        #Note - you will need to change the render_template code segment below to pass in information to the edit.html template (once you have modified edit.html).
        return render_template("edit.html", notebook = data)
    
    #POST:
    elif request.method == "POST":
        #Your code here - what should happen when the user submits their edited review (for the review with the given id)?
        # 
        name = request.form["name"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE notebooks SET name = %s WHERE id = %s",
                    (name, id))
        
        conn.commit()
        cur.close()
        conn.close()
        #Note - no need to change the code below - this will redirect the user back to the reviews page once they"ve submitted their edited review. 
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)