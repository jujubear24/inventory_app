from typing import Dict, Any

def validate_product_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate product form data.
    
    Args:
        data: Dictionary containing product form data
        
    Returns:
        Dictionary of error messages (empty if no errors)
    """
    errors: Dict[str, str] = {}
    
    # Validate required fields
    if not data.get('name'):
        errors['name'] = "Name is required"
    if not data.get('sku'):
        errors['sku'] = "SKU is required"
        
    # Validate numeric fields
    try:
        if data.get('price'):
            float(data['price'])
    except ValueError:
        errors['price'] = "Price must be a number"
        
    try:
        if data.get('stock_level'):
            int(data['stock_level'])
    except ValueError:
        errors['stock_level'] = "Stock level must be an integer"
        
    try:
        if data.get('low_stock_threshold'):
            int(data['low_stock_threshold'])
    except ValueError:
        errors['low_stock_threshold'] = "Low stock threshold must be an integer"
        
    return errors
