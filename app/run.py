from app import create_app

# from app.controllers.auth_controller import auth_bp

app = create_app()

if __name__ == "__main__":
    app.run(threaded=True)
