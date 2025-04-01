from app.services.inventory_service import InventoryService

def test_get_low_stock_products(app, sample_products):
    """Test getting low stock products."""
    with app.app_context():
        # Set the second product to low stock
        sample_products[1].stock_level = sample_products[1].low_stock_threshold - 1
        
        # Get low stock products
        low_stock_products = InventoryService.get_low_stock_products()
        
        # Check that only the low stock product is returned
        assert len(low_stock_products) == 1
        assert low_stock_products[0].id == sample_products[1].id

def test_calculate_inventory_value(app, sample_products):
    """Test calculating total inventory value."""
    with app.app_context():
        # Calculate expected value manually
        expected_value = sum(p.price * p.stock_level for p in sample_products)
        
        # Get calculated value from service
        total_value = InventoryService.calculate_inventory_value()
        
        # Check that values match
        assert total_value == expected_value

def test_adjust_stock(app, sample_products):
    """Test adjusting stock levels."""
    with app.app_context():
        product_id = sample_products[0].id
        original_stock = sample_products[0].stock_level
        
        # Add stock
        product = InventoryService.adjust_stock(product_id, 10)
        assert product.stock_level == original_stock + 10
        
        # Remove stock
        product = InventoryService.adjust_stock(product_id, -5)
        assert product.stock_level == original_stock + 5
        
        # Try to remove too much stock
        product = InventoryService.adjust_stock(product_id, -1000)
        assert product.stock_level == 0  # Should not go below zero
