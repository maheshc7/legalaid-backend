# app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.controllers.controller import main_app

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(main_app)
    return app
