import secrets
from flask import Flask, render_template

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/catalog/')
def catalog():
    return render_template('catalog.html')

@app.route('/notebookinfo/')
def notebookinfo():
    return render_template('notebookinfo.html')

@app.route('/upload/')
def upload():
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)