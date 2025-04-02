"""Test the product service."""
from app.services.product_service import ProductService

def test_create_product_successful(app):
    """Test successfully creating a product."""
    with app.app_context():
        product_data = {
            'name': 'Test Product',
            'sku': 'TST001',
            'description': 'Test description',
            'price': '29.99',
            'stock_level': '100',
            'low_stock_threshold': '20'
        }
        
        product, errors = ProductService.create_product(product_data)
        
        assert errors == {}
        assert product is not None
        assert product.name == 'Test Product'
        assert product.sku == 'TST001'
        assert product.description == 'Test description'
        assert product.price == 29.99
        assert product.stock_level == 100
        assert product.low_stock_threshold == 20

def test_create_product_validation_error(app):
    """Test product creation with validation errors."""
    with app.app_context():
        # Missing required fields
        product_data = {
            'description': 'Test description'
        }
        
        product, errors = ProductService.create_product(product_data)
        
        assert product is None
        assert 'name' in errors
        assert 'sku' in errors

def test_validate_product_data_required_fields(app):
    """Test validation of required fields."""
    with app.app_context():
        # Test with missing fields
        data = {}
        errors = ProductService.validate_product_data(data)
        
        assert 'name' in errors
        assert 'sku' in errors
        
        # Test with empty fields
        data = {'name': '', 'sku': ''}
        errors = ProductService.validate_product_data(data)
        
        assert 'name' in errors
        assert 'sku' in errors

def test_validate_product_data_numeric_fields(app):
    """Test validation of numeric fields."""
    with app.app_context():
        # Test with invalid price
        data = {
            'name': 'Test Product', 
            'sku': 'TST001',
            'price': 'not-a-number'
        }
        errors = ProductService.validate_product_data(data)
        assert 'price' in errors
        
        # Test with invalid stock level
        data = {
            'name': 'Test Product', 
            'sku': 'TST001',
            'stock_level': 'not-a-number'
        }
        errors = ProductService.validate_product_data(data)
        assert 'stock_level' in errors
        
        # Test with invalid threshold
        data = {
            'name': 'Test Product', 
            'sku': 'TST001',
            'low_stock_threshold': 'not-a-number'
        }
        errors = ProductService.validate_product_data(data)
        assert 'low_stock_threshold' in errors

