import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from mains import * 
from auth import *

app = Flask(__name__)
app.config.from_object(__name__)

app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///accounts.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.urandom(12).hex()

db.init_app(app)
login_manager.init_app(app)


with app.app_context():

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    db.create_all()

if __name__ == "__main__":
    print('################### Restarting ###################')
    app.run(host='0.0.0.0', port=4005, debug=False)
