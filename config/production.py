from .default import Config
import os 

class ProductionConfig(Config):
    ENV = 'production'
    DEBUG=False
    
    SECRET_KEY = os.environ.get("SECRET_KEY")


    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Additional security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True

