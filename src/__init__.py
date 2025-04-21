from flask import Flask
from flask_cors import CORS
from src.routes import bp
from src.init_db import create_table

def create_app():
    app = Flask(__name__)
    CORS(app)  
    create_table()
    app.register_blueprint(bp)
    return app
