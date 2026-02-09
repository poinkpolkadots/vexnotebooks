import os
import psycopg2
import secrets
from flask import Flask, render_template, request, url_for, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ab8fbbb4d79d4120031e203d83d298e0'


secret_key = secrets.token_hex(16)
print(secret_key)

def get_db_connection():
    conn = psycopg2.connect(
        host='drhscit.org', 
        database=os.environ['DB'],
        user=os.environ['DB_UN'], 
        password=os.environ['DB_PW']
    )
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM reviews')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', reviews=data)

#Create a route for the page with the form to submit a review
@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        pages = request.form['pages']
        review = request.form['review']
        date = request.form['date']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO reviews (title, author, pages, review, date)'
                    'VALUES (%s, %s, %s, %s, %s)',
                    (title, author, pages, review, date))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('create.html')


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
