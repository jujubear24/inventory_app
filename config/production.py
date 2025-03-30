# config/production.py
"""Production configuration"""
from .default import Config

class ProductionConfig(Config):
    ENV = 'production'
    # Override with more secure values
    SECRET_KEY = 'this-would-be-a-secure-key-in-real-production'  # Use env vars in practice

