
from flask import Flask

def create_app():
    """
    Application factory function to create and configure the Flask app
    """
    app = Flask(__name__)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app