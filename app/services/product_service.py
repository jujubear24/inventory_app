from app.models import db, Product
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal, InvalidOperation
import logging

# Configure logging
logger = logging.getLogger(__name__)



class ProductService:

     # --- Validate Product Data --- 
    @staticmethod
    def validate_product_data(product_data: Dict[str, Any], product_id: Optional[int] = None) -> Dict[str, str]:
        """
        Validates raw product data.

        Args:
            data: A dictionary containing product attributes (potentially strings).

        Returns:
            A dictionary of validation errors, empty if valid.
            Keys are field names, values are error messages.
        """
        errors: Dict[str, str] = {}

        if product_id is None:
            required_fields = ['name', 'sku']
            for field in required_fields:
                if not product_data.get(field): # Checks for None or empty string
                    errors[field] = f"{field.capitalize()} is required."
        elif product_data.get('name') == '': 
            errors['name'] = "Name cannot be empty."
        elif product_data.get('sku') == '': 
             errors['sku'] = "SKU cannot be empty."

        # --- Numeric Fields ---
        numeric_fields = {
            'price': "Price must be a valid number.",
            'stock_level': "Stock level must be a valid integer.",
            'low_stock_threshold': "Low stock threshold must be a valid integer."
        }

        for field, error_message in numeric_fields.items():
            # Only validate if the field is present in the update data
            if field in product_data:
                value_str = product_data.get(field)
                
                if value_str is None or value_str == '':
                    errors[field] = f"{field.capitalize()} cannot be empty if provided."
                    continue # Skip further checks for this field

                try:
                    if field == 'price':
                        val = Decimal(value_str)
                        if val < 0:
                             errors[field] = "Price cannot be negative."
                    else:
                        val = int(value_str)
                        if val < 0:
                             errors[field] = f"{field.capitalize()} cannot be negative."
                except (InvalidOperation, ValueError, TypeError):
                    errors[field] = error_message
            
        # --- SKU Uniqueness Check -- 
        sku = product_data.get('sku')
        if sku: # Only check if SKU is being provided/changed
            query = Product.query.filter(Product.sku == sku)
            if product_id is not None:
                query = query.filter(Product.id != product_id)
            existing_product_with_sku = query.first()
            if existing_product_with_sku:
                errors['sku'] = "This SKU is already in use by another product."

        return errors


    @staticmethod
    def create_product(product_data: Dict[str, Any]) -> Tuple[Product, Dict[str, str]]:
        """
        Creates a new product after validation.

        Args:
            data: Dictionary containing product attributes.

        Returns:
            A tuple containing (Product object or None, dictionary of errors).
        """

        # validate product data
        errors = ProductService.validate_product_data(product_data)
        if errors:
            return None, errors

       
        try:
            # Converts data types after validation
            price = Decimal(product_data.get('price', '0'))
            stock_level = int(product_data.get('stock_level', 0))
            low_stock_threshold = int(product_data.get('low_stock_threshold', 0))

            product = Product(
                name=product_data.get('name'),
                sku=product_data.get('sku'),
                description=product_data.get('description', ''),
                price=price,
                stock_level=stock_level,
                low_stock_threshold=low_stock_threshold
            )
            db.session.add(product)
            db.session.commit()
            logger.info(f"Product created successfully: {product.sku}")
            return product, {} # Return product and empty error dict on success


        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"Data conversion error during product creation: {e}", exc_info=True)
            return None, {'_conversion': f"Error converting numeric fields: {e}"}
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during product creation: {e}", exc_info=True)
            return None, {'_database': "A database error occurred while creating the product."}
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
         """Gets a product by its ID using the efficient 'get' method."""

         logger.debug(f"Attempting to retrieve product with ID: {product_id}")
         product = db.session.get(Product, product_id)
         if product:
             logger.debug(f"Product found: {product.sku}")
         else:
             logger.debug(f"Product with ID {product_id} not found.")
         return product

    
    @staticmethod
    def update_product(product_id: int, product_data: Dict[str, Any]) -> Tuple[Optional[Product], Dict[str, str]]:
        """
        Updates an existing product after validation.

        Args:
            product_id: The ID of the product to update.
            data: Dictionary containing attributes to update. Can be partial.

        Returns:
            A tuple containing (Updated Product object or None, dictionary of errors).
        """
        logger.info(f"Attempting to update product ID: {product_id} with data: {product_data}")
        product = ProductService.get_product_by_id(product_id)
        if not product:
            logger.warning(f"Update failed: Product with ID {product_id} not found.")
            return None, {'_system': 'Product not found'}

        # Validate the incoming data, passing the product_id for context (e.g., SKU check)
        errors = ProductService.validate_product_data(product_data, product_id=product_id)
        if errors:
            logger.warning(f"Validation failed for product update ID {product_id}: {errors}")
            return None, errors

        # Update attributes if they are present in the data dictionary
        updated = False
        try:
            if 'name' in product_data and product.name != product_data['name']:
                product.name = product_data['name']
                updated = True
            if 'sku' in product_data and product.sku != product_data['sku']:
                product.sku = product_data['sku']
                updated = True
            if 'description' in product_data and product.description != product_data['description']:
                product.description = product_data.get('description', '') # Allow setting empty description
                updated = True
            if 'price' in product_data:
                new_price = Decimal(product_data['price'])
                if product.price != new_price:
                    product.price = new_price
                    updated = True
            if 'stock_level' in product_data:
                new_stock = int(product_data['stock_level'])
                if product.stock_level != new_stock:
                    product.stock_level = new_stock
                    updated = True
            if 'low_stock_threshold' in product_data:
                new_threshold = int(product_data['low_stock_threshold'])
                if product.low_stock_threshold != new_threshold:
                    product.low_stock_threshold = new_threshold
                    updated = True

            if not updated:
                 logger.info(f"No changes detected for product ID: {product_id}")
                 return product, {} # No changes, return success but indicate no update needed

            db.session.add(product) # Add the modified object to the session
            db.session.commit()
            logger.info(f"Product updated successfully: {product.sku} (ID: {product_id})")
            return product, {}

        except (InvalidOperation, ValueError, TypeError) as e:
             db.session.rollback() # Rollback on conversion error during update
             logger.error(f"Data conversion error during product update ID {product_id}: {e}", exc_info=True)
             return None, {'_conversion': f"Error converting numeric fields during update: {e}"}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during product update ID {product_id}: {e}", exc_info=True)
            return None, {'_database': "A database error occurred while updating the product."}

    # Add other necessary service methods, e.g., delete_product, get_all_products...
    # @staticmethod
    # def delete_product(product_id: int) -> bool:
    #     """Deletes a product by ID. Returns True on success, False otherwise."""
    #     product = ProductService.get_product_by_id(product_id)
    #     if product:
    #         try:
    #             db.session.delete(product)
    #             db.session.commit()
    #             logger.info(f"Product deleted successfully: ID {product_id}")
    #             return True
    #         except Exception as e:
    #             db.session.rollback()
    #             logger.error(f"Database error deleting product ID {product_id}: {e}", exc_info=True)
    #             return False
    #     else:
    #         logger.warning(f"Delete failed: Product ID {product_id} not found.")
    #         return False
    
   
        
   