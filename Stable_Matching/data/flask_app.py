import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

domain = '127.0.0.1'

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'main.login'

app = Flask(__name__)
app.secret_key = 'test123'
app.config['SESSION_TYPE'] = 'filesystem'
app.static_folder = 'static'
login_manager.init_app(app)

path_to_db = __file__.split('\\')
path_to_db.pop(-1)
path_to_db = '\\'.join(path_to_db)
path_to_db = os.path.join(path_to_db, "central_database.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path_to_db
db = SQLAlchemy(app)
