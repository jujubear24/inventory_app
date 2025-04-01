import os
from typing import Dict, Any, Optional
from datetime import datetime

def generate_sku(product_name: str, category: Optional[str] = None) -> str:
    """Generate a SKU from a product name.
    
    Args:
        product_name: Name of the product
        category: Optional category prefix
        
    Returns:
        Generated SKU
    """
    prefix = category[:3].upper() if category else ""
    name_part = ''.join(c for c in product_name if c.isalnum())[:5].upper()
    timestamp = datetime.now().strftime('%y%m%d')
    return f"{prefix}{name_part}{timestamp}"

def get_app_config() -> Dict[str, Any]:
    """Get application configuration based on environment.
    
    Returns:
        Dictionary of configuration values
    """
    env = os.environ.get('FLASK_ENV', 'development')
    config = {
        'CACHE_BUSTER': datetime.now().timestamp()
    }
    
    return config
