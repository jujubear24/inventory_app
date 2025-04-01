# tests/test_routes/test_products.py
"""Test the product-related routes."""

def test_add_product_get(client):
    """Test the add product form route (GET)."""
    response = client.get('/products/add')
    assert response.status_code == 200
    assert b'Add New Product' in response.data

def test_add_product_post(client, app):
    """Test adding a new product (POST)."""
    response = client.post(
        '/products/add',
        data={
            'name': 'New Test Product',
            'sku': 'NTP001',
            'description': 'A new test product',
            'price': '15.99',
            'stock_level': '25',
            'low_stock_threshold': '5'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    # Check that the product appears in the list
    assert b'New Test Product' in response.data

def test_edit_product(client, sample_products):
    """Test editing a product."""
    product_id = sample_products[0].id
    response = client.post(
        f'/products/edit/{product_id}',
        data={
            'name': 'Updated Product Name',
            'sku': sample_products[0].sku,
            'description': 'Updated description',
            'price': '99.99',
            'stock_level': '50',
            'low_stock_threshold': '10'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Updated Product Name' in response.data

def test_delete_product(client, sample_products, app):
    """Test deleting a product."""
    product_id = sample_products[0].id
    product_name = sample_products[0].name
    
    response = client.get(
        f'/products/delete/{product_id}',
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Product name should no longer be in the response
    assert product_name.encode() not in response.data

def test_stock_in(client, sample_products, app):
    """Test adding stock to a product."""
    product_id = sample_products[0].id
    original_stock = sample_products[0].stock_level
    
    response = client.post(
        f'/products/stock/in/{product_id}',
        data={'quantity': '5'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Check if stock was updated
    with app.app_context():
        from app.models import Product
        updated_product = Product.query.get(product_id)
        assert updated_product.stock_level == original_stock + 5

def test_stock_out(client, sample_products, app):
    """Test removing stock from a product."""
    product_id = sample_products[0].id
    original_stock = sample_products[0].stock_level
    
    response = client.post(
        f'/products/stock/out/{product_id}',
        data={'quantity': '5'},
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # Check if stock was updated
    with app.app_context():
        from app.models import Product
        updated_product = Product.query.get(product_id)
        assert updated_product.stock_level == original_stock - 5

