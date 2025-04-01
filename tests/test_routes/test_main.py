"""Test the main routes."""

def test_product_list(client, sample_products):
    """Test the product list (dashboard) route."""
    response = client.get('/')
    assert response.status_code == 200
    # Check that all products are shown
    for product in sample_products:
        assert product.name.encode() in response.data

def test_inventory_status(client, sample_products):
    """Test the inventory status route."""
    response = client.get('/inventory_status')
    assert response.status_code == 200
    # Check that all products are shown
    for product in sample_products:
        assert product.name.encode() in response.data

