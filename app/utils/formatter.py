from typing import Union, List, Dict, Any

def format_currency(value: Union[float, int]) -> str:
    """Format a value as currency.
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted currency string
    """
    return f"${value:.2f}"
    
def calculate_inventory_stats(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate inventory statistics.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Dictionary of statistics
    """
    total_products = len(products)
    total_value = sum(p.price * p.stock_level for p in products) if products else 0
    avg_stock = sum(p.stock_level for p in products) / total_products if total_products > 0 else 0
    low_stock_count = sum(1 for p in products if p.stock_level <= p.low_stock_threshold)
    out_of_stock_count = sum(1 for p in products if p.stock_level <= 0)
    
    return {
        'total_products': total_products,
        'total_value': total_value,
        'avg_stock': round(avg_stock, 1),
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    }
