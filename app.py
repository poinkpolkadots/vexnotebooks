import secrets
from init_db import get_db_connection
from flask import *
from data import *

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)

if __name__ == "__main__":
    app.run(debug=True)