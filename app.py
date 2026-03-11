import secrets
from flask import Flask, render_template
from util import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

if __name__ == "__main__":
    app.run(debug=True)