from flask_cors import CORS
from app import create_app
from app.controllers.controller import main_app

# from app.controllers.auth_controller import auth_bp

app = create_app()
CORS(app)

app.register_blueprint(main_app)

if __name__ == "__main__":
    app.run(threaded=True)
