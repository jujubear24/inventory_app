from flask import Flask, render_template
from app.models.db import db 
import os
from app.utils import get_app_config
from config import get_config
from flask_login import LoginManager


def create_app(config_name=None):
    """Application factory for creating Flask app instances"""
    
    app = Flask(__name__, instance_relative_config=True)
    
    # Get the appropriate config class
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app.config.from_object(get_config(config_name))
    
    # Load instance config (if it exists)
    app.config.from_pyfile('config.py', silent=True)

    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{app.instance_path}/inventory.db'

    #  Utility config
    app.config.update(get_app_config())
    
    # Initialize db with the app
    db.init_app(app)

    # Register CLI command for database initialization
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        with app.app_context():
            db.create_all()
        print("Initialized the database.")
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))


    
    # Register blueprints
    from app.routes import main_bp, products_bp, reports_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Register error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # Rollback any failed database sessions
        return render_template('errors/500.html'), 500
    




    
    # Create instance folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    return app




