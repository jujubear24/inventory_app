from .default import Config

class DevelopmentConfig(Config):
    DEBUG = True
    # This will output mail to console
    MAIL_DEBUG = True

    MAIL_SUPPRESS_SEND = True

    MAIL_SERVER = "localhost"  # Dummy server
    MAIL_PORT = 25  # Dummy port, or a common dev port like 25, 587
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
