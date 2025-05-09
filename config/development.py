from .default import Config

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_BACKEND = "console"  # This will output mail to console


