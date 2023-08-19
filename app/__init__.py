# app/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask

def create_app():
    app = Flask(__name__)
    load_dotenv() 
    app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    # Configure the app, register blueprints, etc.

    return app
