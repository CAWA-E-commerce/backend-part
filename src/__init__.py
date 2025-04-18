from flask import Flask
from src.routes import bp
from src.init_db import create_table

def create_app():
    app = Flask(__name__)
    create_table()
    app.register_blueprint(bp)
    return app
