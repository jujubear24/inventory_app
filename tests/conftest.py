"""Pytest configuration and fixtures."""
import pytest
from app import app as flask_app
from models import db, Product

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    flask_app.config.from_pyfile('test_config.py')
    
    # Create context, database and tables
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def sample_products(app):
    """Create sample products for testing."""
    with app.app_context():
        # Create some test products
        products = [
            Product(
                name='Test Product 1',
                sku='TP001',
                description='Test description 1',
                price=10.99,
                stock_level=20,
                low_stock_threshold=5
            ),
            Product(
                name='Test Product 2',
                sku='TP002',
                description='Test description 2',
                price=20.50,
                stock_level=3,
                low_stock_threshold=5
            ),
            Product(
                name='Test Product 3',
                sku='TP003',
                description='Test description 3',
                price=30.75,
                stock_level=0,
                low_stock_threshold=5
            )
        ]
        
        db.session.add_all(products)
        db.session.commit()
        
        yield products
        
        # Clean up
        for product in products:
            db.session.delete(product)
        db.session.commit()

