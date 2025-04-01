from app.models import Product

def test_product_creation(app):
    """Test that we can create a product."""
    with app.app_context():
        product = Product(
            name='Test Model Product',
            sku='TMP001',
            description='A test product for model testing',
            price=9.99,
            stock_level=100,
            low_stock_threshold=20
        )
        
        # Test properties directly
        assert product.name == 'Test Model Product'
        assert product.sku == 'TMP001'
        assert product.price == 9.99
        assert product.stock_level == 100
        assert product.low_stock_threshold == 20

def test_product_repr(app, sample_products):
    """Test the string representation of a product."""
    product = sample_products[0]
    assert str(product) == f'<Product {product.name}>'

def test_low_stock_detection(app):
    """Test that we can correctly identify low stock products."""
    with app.app_context():
        # Normal stock
        normal_product = Product(name='Normal Stock', sku='NS001', 
                                price=10.0, stock_level=20, 
                                low_stock_threshold=10)
        
        # Low stock
        low_product = Product(name='Low Stock', sku='LS001', 
                            price=10.0, stock_level=5, 
                            low_stock_threshold=10)
        
        # Out of stock
        out_product = Product(name='Out of Stock', sku='OS001', 
                            price=10.0, stock_level=0, 
                            low_stock_threshold=10)
        
        # Test low stock condition
        assert low_product.stock_level <= low_product.low_stock_threshold
        assert normal_product.stock_level > normal_product.low_stock_threshold
        assert out_product.stock_level <= out_product.low_stock_threshold
