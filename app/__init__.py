# os and Dotenv Loading
import os
from dotenv import load_dotenv


# Flask and related
from flask import Flask, render_template, flash  


# Extensions
from flask_migrate import Migrate  
from flask_login import LoginManager, current_user, login_user  
from flask_dance.contrib.google import make_google_blueprint  
from flask_dance.consumer import oauth_authorized  
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage  

# Local App Components (Config, DB, Models)
from config import get_config  
from app.models.db import db  
from app.models.user import User 
from app.utils import get_app_config 
from app.models.oauth import OAuth  


load_dotenv()

# App factory to create Flask app instances
def create_app(config_name=None):
    """Application factory for creating Flask app instances"""
    
    app = Flask(__name__, instance_relative_config=True)

     # Load configuration from config object based on FLASK_ENV
    selected_config = get_config(config_name)
    app.config.from_object(selected_config)
    print(f"--- FLASK DEBUG: Loaded SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')} ---")
    app.config.update(get_app_config())

   

    if not app.config.get("SECRET_KEY"):
        app.logger.error("FATAL ERROR: SECRET_KEY environment variable is not set.")
        raise ValueError("SECRET_KEY is not configured. Cannot start application without it. Set the SECRET_KEY environment variable.")
    
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
         app.logger.warning("SQLALCHEMY_DATABASE_URI environment variable is not set.")
    
    # Ensure Google OAuth keys are set
    if not app.config.get("GOOGLE_OAUTH_CLIENT_ID") or not app.config.get("GOOGLE_OAUTH_CLIENT_SECRET"):
        app.logger.warning("Google OAuth Client ID or Secret not configured. Google login will not work.")
    
    google_keys_set = app.config.get("GOOGLE_OAUTH_CLIENT_ID") and app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not google_keys_set:
         app.logger.warning("Google OAuth secrets not set. Google login will be disabled.")
    
    # Initialize db with the app
    db.init_app(app)
    Migrate(app, db)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))



    # Register CLI command for database initialization
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        with app.app_context():
            db.create_all()
        print("Initialized the database.")
    

     # --- Flask-Dance Google Blueprint Setup ---
    # Only register if keys are configured
    google_bp = None
    if google_keys_set:
        google_bp = make_google_blueprint(
            client_id=app.config.get("GOOGLE_OAUTH_CLIENT_ID"),
            client_secret=app.config.get("GOOGLE_OAUTH_CLIENT_SECRET"),
            scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
            storage=SQLAlchemyStorage(OAuth, db.session, user=current_user), 
            # offline=True, # Add if you need refresh tokens
        )
        app.register_blueprint(google_bp, url_prefix="/login")
    else:
        google_bp = None


    
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
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # --- OAuth Authorized Signal Handler ---
    if google_keys_set and 'google' in app.blueprints:
        @oauth_authorized.connect_via(app.blueprints['google']) # Connect to the google blueprint if it was created
        def google_logged_in(blueprint, token):
            if not token:
                flash("Failed to log in with Google.", category="error")
                return False # Prevents Flask-Dance default redirect

            try:
                # Get user info from Google
                resp = blueprint.session.get("/oauth2/v1/userinfo")
                resp.raise_for_status() # Raise exception for bad responses (4xx, 5xx)
                google_info = resp.json()
                
            except Exception as e:
                app.logger.error(f"Failed to fetch user info from Google: {e}")
                flash("Failed to fetch user info from Google.", category="error")
                return False

            google_user_id = str(google_info.get("id"))
            email = google_info.get("email")

            if not google_user_id or not email:
                flash("Could not retrieve sufficient information from Google.", category="error")
                return False

            # Find this OAuth token in the database
            try:
                oauth_entry = OAuth.query.filter_by(
                    provider=blueprint.name, provider_user_id=google_user_id
                ).one_or_none() # Use one_or_none for clarity

                if oauth_entry:
                    # OAuth connection exists, log in the associated user
                    login_user(oauth_entry.user)
                    oauth_entry.token = token
                    db.session.add(oauth_entry)
                    db.session.commit()
                    flash("Successfully signed in with Google.", category="success")

                else:
                    # No existing OAuth connection
                    user = User.query.filter_by(email=email).one_or_none()

                    if user:
                        # User with this email exists, link the OAuth account
                        oauth_entry = OAuth(provider=blueprint.name, provider_user_id=google_user_id, token=token, user=user)
                        db.session.add(oauth_entry)
                        db.session.commit()
                        login_user(user)
                        flash("Successfully signed in with Google and linked account.", category="success")
                    else:
                        # No user with this email, create a new user
                        new_user = User(email=email, username=email.split('@')[0])
                        oauth_entry = OAuth(provider=blueprint.name, provider_user_id=google_user_id, token=token, user=new_user)
                        db.session.add_all([new_user, oauth_entry])
                        db.session.commit()
                        login_user(new_user)
                        flash("Successfully registered and signed in with Google.", category="success")

            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error during OAuth callback processing: {e}")
                flash("An error occurred during Google Sign-In.", category="danger")
                return False # Prevent redirect on error

            return False # Return False to handle redirection manually if needed (e.g., flash message first)
    
    return app




