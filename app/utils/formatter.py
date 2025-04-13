from typing import Union, List, Dict, Any
from decimal import Decimal, InvalidOperation
from flask import current_app

def format_currency(value: Union[float, int, Decimal]) -> str:
    """Format a value as currency"""
   
    return f"${value:.2f}"
    
def calculate_inventory_stats(products: List[Any]) -> Dict[str, Any]:
    """Calculate inventory statistics using a single loop."""

    total_products = 0
    total_value = Decimal(0)
    total_stock_level = 0
    low_stock_count = 0
    out_of_stock_count = 0

    if products: # Only loop if there are products
        for p in products:
            total_products += 1
           
            try:
                if p.price is None:
                    raise ValueError("Product price is None")
                
                current_value = Decimal(p.price) * Decimal(p.stock_level) 
                total_value += current_value

            
            except (TypeError, ValueError, InvalidOperation) as e:
                # Log a warning if calculation fails for a specific product
                # Attempt to get SKU or ID for logging, fall back gracefully
                product_identifier = getattr(p, 'sku', getattr(p, 'id', 'unknown'))
                current_app.logger.warning(
                    f"Could not calculate value for product '{product_identifier}': {e}. Skipping value.",
                    exc_info=False # Set to True if you want the full traceback in logs
                )
            
            try:
                
                total_stock_level += int(p.stock_level)
            except (TypeError, ValueError):
                product_identifier = getattr(p, 'sku', getattr(p, 'id', 'unknown'))
                current_app.logger.warning(
                    f"Invalid stock level for product '{product_identifier}': {p.stock_level}. Skipping stock level sum for this item.",
                    exc_info=False
                )
            
            try:
                stock = int(p.stock_level)
                low_thresh = int(p.low_stock_threshold)
                if stock <= 0:
                    out_of_stock_count += 1
                    if low_thresh >= 0: 
                        low_stock_count += 1
                elif stock <= low_thresh:
                    low_stock_count += 1
            except (TypeError, ValueError):
                 pass

    # Calculate average after the loop
    avg_stock = (Decimal(total_stock_level) / Decimal(total_products)) if total_products > 0 else Decimal(0)

    return {
        'total_products': total_products,
        'total_value': total_value,
        'avg_stock': round(float(avg_stock), 1), 
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    }