import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_restful import Api
current_dir=os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
#key is defined under seperate file in order to maintain security please create a keys.py file and define config key inside it
from library import keys
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(current_dir,"system.db")

app.config['UPLOAD_FOLDER'] = './library/uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
api = Api(app)
import library.routes