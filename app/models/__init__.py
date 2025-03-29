# app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Initialize db here, but it will be configured in app/__init__.py
db = SQLAlchemy()

# Import models to make them available from the models package
from .product import Product

# Export all models
__all__ = ['db', 'Product']
