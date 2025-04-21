from flask import Flask
from src.routes.routes import bp
from src.init_db import create_table
from flask_cors import CORS
import os

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), '.', 'static'),
        static_url_path='/static'
    )
    
    create_table()
    CORS(app)
    app.register_blueprint(bp)
    
    return app
