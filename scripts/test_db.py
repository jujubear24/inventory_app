from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

DATABASE_URI = 'sqlite:///instance/inventory.db'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Print the absolute path to help debug
relative_db_path = DATABASE_URI.replace('sqlite:///', '')
absolute_db_path = os.path.abspath(relative_db_path)
db_directory = os.path.dirname(absolute_db_path)


print("--- Database Debug Info ---")
print(f"SQLALCHEMY_DATABASE_URI: {DATABASE_URI}")
print(f"Relative DB Path: {relative_db_path}")
print(f"Absolute DB Path Resolved: {absolute_db_path}")
print(f"Expected DB Directory: {db_directory}")
print(f"DB Directory Exists? : {os.path.exists(db_directory)}")

print(f"DB Directory Writable?: {os.access(db_directory, os.W_OK)}")

print("---------------------------")

db = SQLAlchemy(app)

try:
    with app.app_context():
    
        print("Attempting db.create_all()...")
        # Include models here if necessary for create_all, otherwise it might do nothing
        # db.create_all() # Might need specific models if using Migrate context usually
        # Let's just try connecting implicitly by executing a simple query
        result = db.session.execute(db.text("SELECT 1")).scalar()
        if result == 1:
            print("Successfully connected to the database and executed a query.")
        else:
            print("Connected but query failed.")

except Exception as e:
    print(f"\n!!! Error occurred: {e}")

