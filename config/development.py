"""Development configuration"""
from .default import Config

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

