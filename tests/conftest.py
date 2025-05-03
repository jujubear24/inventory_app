import pytest
from app import create_app
from app.models import db, Product

@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Creates and yields an application context for tests."""
    with app.app_context() as ctx: 
        print(f"DEBUG: Yielding app_context: {ctx}") # Optional debug print
        yield ctx 



@pytest.fixture
def sample_products(app):
    """Create sample products for testing."""
    with app.app_context():
        products = [
            Product(
                name='Test Product 1',
                sku='TP001',
                description='First test product',
                price=10.99,
                stock_level=50,
                low_stock_threshold=10
            ),
            Product(
                name='Test Product 2',
                sku='TP002',
                description='Second test product',
                price=20.99,
                stock_level=5,
                low_stock_threshold=10
            )
        ]
        
        db.session.add_all(products)
        db.session.commit()
        
        yield products
        
        # Clean up
        for product in products:
            # Check if the product still exists before deleting
            existing_product = db.session.query(Product).get(product.id)
            if existing_product:
                db.session.delete(existing_product)
        db.session.commit()


