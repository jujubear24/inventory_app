from app.models import db, Product
from typing import Dict, Any, Tuple

class ProductService:
    @staticmethod
    def create_product(product_data: Dict[str, Any]) -> Tuple[Product, Dict[str, str]]:
        """Create a new product with validation."""
        errors = ProductService.validate_product_data(product_data)
        if errors:
            return None, errors
            
        product = Product(
            name=product_data.get('name'),
            sku=product_data.get('sku'),
            description=product_data.get('description', ''),
            price=float(product_data.get('price', 0)),
            stock_level=int(product_data.get('stock_level', 0)),
            low_stock_threshold=int(product_data.get('low_stock_threshold', 10))
        )
        
        db.session.add(product)
        db.session.commit()
        return product, {}
        
    @staticmethod
    def validate_product_data(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate product data and return errors."""
        errors = {}
        
        # Validate required fields
        if not data.get('name'):
            errors['name'] = "Name is required"
        if not data.get('sku'):
            errors['sku'] = "SKU is required"
        
        # Validate numeric fields
        if data.get('price'):
            try:
                float(data['price'])
            except ValueError:
                errors['price'] = "Price must be a number"
        
        if data.get('stock_level'):
            try:
                int(data['stock_level'])
            except ValueError:
                errors['stock_level'] = "Stock level must be an integer"
            
        if data.get('low_stock_threshold'):
            try:
                int(data['low_stock_threshold'])
            except ValueError:
                errors['low_stock_threshold'] = "Low stock threshold must be an integer"
        
        return errors
