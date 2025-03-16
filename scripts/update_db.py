# update_db.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db

with app.app_context():
    db.create_all()

print("Database updated successfully!") #add a success message.