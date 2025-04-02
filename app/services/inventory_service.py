from app.models import db, Product
from typing import List, Optional

class InventoryService:
    @staticmethod
    def get_low_stock_products() -> List[Product]:
        """Get all products with stock below their threshold."""
        return Product.query.filter(
            Product.stock_level <= Product.low_stock_threshold
        ).all()
        
    @staticmethod
    def calculate_inventory_value() -> float:
        """Calculate the total value of all inventory."""
        products = Product.query.all()
        return sum(product.price * product.stock_level for product in products)
    
    @staticmethod
    def adjust_stock(product_id: int, quantity: int) -> Optional[Product]:
        """Adjust stock level for a product."""
        product = db.session.get(Product, product_id)
        if not product:
            return None
            
        product.stock_level += quantity
        if product.stock_level < 0:
            product.stock_level = 0
            
        db.session.commit()
        return product
