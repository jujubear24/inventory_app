from app.models import db, Product
from typing import Dict, Any, Tuple

class ProductService:
    @staticmethod
    def create_product(product_data: Dict[str, Any]) -> Tuple[Product, Dict[str, str]]:
        """Create a new product"""

        try:
            product = Product(
                name=product_data.get('name'),
                sku=product_data.get('sku'),
                description=product_data.get('description', ''),
                # Ensure type conversion if necessary, though WTForms should handle it
                price=float(product_data.get('price', 0)),
                stock_level=int(product_data.get('stock_level', 0)),
                low_stock_threshold=int(product_data.get('low_stock_threshold', 10))
            )

            db.session.add(product)
            db.session.commit()
            return product, {} # Return product and empty error dict on success
        
        except Exception as e:
             db.session.rollback()
             # Log the error e
             return None, {'database': f'Error saving product: {str(e)}'}
    
        
   