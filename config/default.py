# config/default.py
"""Default configuration"""

class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'dev-key'  # Change this in production!
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/inventory.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
