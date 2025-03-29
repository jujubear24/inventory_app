from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()

def create_app(config_name=None):
    """Application factory for creating Flask app instances"""
    
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_object('config.default')
    
    # Load environment specific configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(f'config.{config_name}')
    
    # Load instance config (if it exists)
    app.config.from_pyfile('config.py', silent=True)
    
    # Initialize extensions with the app
    db.init_app(app)
    
    # Register blueprints
    from app.routes import main_bp, products_bp, reports_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(reports_bp)
    
    # Create instance folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    return app

