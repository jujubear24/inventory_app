from .default import Config
import os 

class ProductionConfig(Config):
    DEBUG=False

    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Additional security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True  

    # Ensure MAIL_BACKEND is not set to 'console' for production.
    # MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_USE_TLS/SSL
    # should be set via environment variables.
    MAIL_SUPPRESS_SEND = False
