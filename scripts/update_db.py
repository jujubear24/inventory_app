# update_db.py
import sys
import os


# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db

def update_database() -> None:
    """Create or update all database tables based on model definitions."""
    with app.app_context():
        db.create_all()
    print("Database updated successfully!")  # add a success message.

if __name__ == "__main__":
    update_database()

