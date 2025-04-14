import os 

class Config:

     # --- Read Secrets and Essential Config from Environment ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')

    # --- Other Common Base Settings (Non-Secrets) ---
    SQLALCHEMY_TRACK_MODIFICATIONS = False
