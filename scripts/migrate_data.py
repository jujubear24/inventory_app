"""Convert low_stock_threshold from string to integer

This script should be run as a one-time fix to ensure all low_stock_threshold
values in the Product table are properly stored as integers.
"""
from typing import Any, List
import sys
import os 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import Product
from app.models.db import db



def run_migration() -> None:
    app  = create_app()
    with app.app_context():
        # Get all products
        products: List[Product] = Product.query.all()
        
        # Track how many records were updated
        update_count: int = 0
        
        for product in products:
            # Check if the value is not already an integer
            if not isinstance(product.low_stock_threshold, int):
                try:
                    # Try to convert to integer
                    original_value: Any = product.low_stock_threshold
                    product.low_stock_threshold = int(float(original_value))
                    update_count += 1
                    print(f"Updated product {product.id} ({product.name}): {original_value} -> {product.low_stock_threshold}")
                except (ValueError, TypeError):
                    # If conversion fails, set a default value
                    original_value: Any = product.low_stock_threshold
                    product.low_stock_threshold = 10  # Using your model's default
                    update_count += 1
                    print(f"Failed to convert {original_value} for product {product.id} ({product.name}), set to default: 10")
        
        # Save all changes if any were made
        if update_count > 0:
            print(f"Committing {update_count} changes to the database...")
            db.session.commit()
            print("Migration completed successfully!")
        else:
            print("No changes needed, all values already stored as integers.")

if __name__ == "__main__":
    run_migration()


