# app/routes/__init__.py
from .main import main_bp
from .products import products_bp
from .reports import reports_bp

# Export all blueprints for easy import
__all__ = ['main_bp', 'products_bp', 'reports_bp']

