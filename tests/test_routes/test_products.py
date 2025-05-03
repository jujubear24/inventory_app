from app.models.db import db
from app.models import Product
from decimal import Decimal


"""Test the product-related routes."""

def test_add_product_get(client):
    """Test the add product form route (GET)."""
    response = client.get('/products/add')
    assert response.status_code == 200
    expected_text = b'Add Product'
    assert expected_text in response.data, \
        f"Assertion Failed: Expected text '{expected_text.decode()}' was not found in the response HTML for /products/add."
    

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
    with app.app_context():
        product = Product.query.filter_by(sku='NTP001').first()
        assert product is not None
        assert product.name == 'New Test Product'

def test_edit_product(client, sample_products, app):
    """Test editing a product."""

     # Ensure we have products from the fixture
    assert sample_products, "Sample products fixture is empty"
    product_to_edit = sample_products[0]
    product_id = product_to_edit.id

    response = client.post(
        f'/products/edit/{product_id}', # Assuming route is /products/edit/<id>
        data={
            'name': 'Updated Product Name',
            'sku': product_to_edit.sku, # Keep SKU same or provide a new valid one
            'description': 'Updated description',
            'price': '99.99',
            'stock_level': '50',
            'low_stock_threshold': '10'
            # Add CSRF token if enabled and required by form
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    # Check that the updated name appears in the list (assuming redirect to list)
    assert b'Updated Product Name' in response.data
    # Verify in DB
    with app.app_context():
        updated_product = db.session.get(Product, product_id)
        assert updated_product is not None
        assert updated_product.name == 'Updated Product Name'
        assert updated_product.price == Decimal('99.99') # Compare with float or Decimal('99.99') as needed


# --- Test Delete Product
def test_delete_product(client, sample_products, app):
    """Test deleting a product via POST request."""

    assert sample_products, "Sample products fixture is empty"
    product_to_delete = sample_products[0]
    product_id = product_to_delete.id
    product_name = product_to_delete.name

    # --- Simulate POSTing the confirmation form ---
    delete_url = f'/products/delete/{product_id}'

    # Send POST request. Since CSRF is likely disabled in tests,
    response = client.post(
        delete_url,
        follow_redirects=True # Follow redirect to the product list page
    )

    # 1. Check status code after redirect (should be OK)
    assert response.status_code == 200


    # 2. Optional: Check if the success flash message is present
    expected_flash_raw = f'Product "{product_name}" deleted successfully!'
    expected_flash_literal = expected_flash_raw.encode()
    expected_flash_escaped_quot = expected_flash_raw.replace('"', '&quot;').encode()
    expected_flash_escaped_34 = expected_flash_raw.replace('"', '&#34;').encode() 

    assert (expected_flash_literal in response.data or
            expected_flash_escaped_quot in response.data or
            expected_flash_escaped_34 in response.data), \
           f"Expected flash message '{expected_flash_raw}' (literal or escaped with &quot; or &#34;) not found in response."

    # 3. Verify the product is GONE from the database ---
    with app.app_context():
        deleted_product = db.session.get(Product, product_id)
        assert deleted_product is None, f"Product with ID {product_id} ('{product_name}') was not deleted from the database."


def test_stock_in(client, sample_products, app):
    """Test adding stock to a product."""
    assert sample_products, "Sample products fixture is empty"
    product_id = sample_products[0].id
    original_stock = sample_products[0].stock_level

    response = client.post(
        f'/products/stock/in/{product_id}', # Assuming route is /products/stock/in/<id>
        data={'quantity': '5'},
        follow_redirects=True
    )
    assert response.status_code == 200

    # Check if stock was updated in the database
    with app.app_context():
        updated_product = db.session.get(Product, product_id)
        assert updated_product is not None, f"Product {product_id} not found after stock_in."
        assert updated_product.stock_level == original_stock + 5


def test_stock_out(client, sample_products, app):
    """Test removing stock from a product."""
    assert sample_products, "Sample products fixture is empty"
    product_id = sample_products[0].id
    original_stock = sample_products[0].stock_level

    # Ensure there's enough stock to remove
    assert original_stock >= 5, f"Not enough stock ({original_stock}) for product {product_id} to test stock_out."

    response = client.post(
        f'/products/stock/out/{product_id}', # Assuming route is /products/stock/out/<id>
        data={'quantity': '5'},
        follow_redirects=True
    )
    assert response.status_code == 200

    # Check if stock was updated in the database
    with app.app_context():
        updated_product = db.session.get(Product, product_id)
        assert updated_product is not None, f"Product {product_id} not found after stock_out."
        assert updated_product.stock_level == original_stock - 5



