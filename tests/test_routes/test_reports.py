"""Test the report routes."""

def test_low_stock_report(client, sample_products, app):
    """Test the low stock report route."""
    # Ensure one product is at low stock
    with app.app_context():
        sample_products[1].stock_level = sample_products[1].low_stock_threshold - 1
        from app.models import db
        db.session.commit()
    
    # Test the route
    response = client.get('/reports/low_stock')
    assert response.status_code == 200
    
    # Verify that only low stock products are shown
    assert sample_products[1].name.encode() in response.data
    assert sample_products[0].name.encode() not in response.data

def test_product_summary_report(client, sample_products):
    """Test the product summary report route."""
    response = client.get('/reports/product_summary')
    assert response.status_code == 200
    
    # Check that all products are shown and ordered by name
    for product in sample_products:
        assert product.name.encode() in response.data

def test_product_value_report(client, sample_products, app):
    """Test the product value report route."""
    # Calculate expected total value
    expected_total = sum(p.price * p.stock_level for p in sample_products)
    
    response = client.get('/reports/product_value')
    assert response.status_code == 200
    
    # Check that all products are shown
    for product in sample_products:
        assert product.name.encode() in response.data
    
    # Check that total value is shown and formatted correctly
    from app.utils import format_currency
    formatted_value = format_currency(expected_total)
    assert formatted_value.encode() in response.data




