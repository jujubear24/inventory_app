import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env FIRST
load_dotenv()

from app import create_app  # noqa: E402
from app.models import db, Role # noqa: E402

DEFAULT_ROLES = {
    'Admin': 'Administrator with full access',
    'User': 'Standard user role'
    # Add more default roles here 
}

def seed_initial_roles():
    """Checks for default roles in DEFAULT_ROLES and adds any that are missing."""
    print("Seeding initial roles...")
    roles_added_count = 0
    try:
        for name, description in DEFAULT_ROLES.items():
            role = Role.query.filter_by(name=name).first()
            if not role:
                new_role = Role(name=name, description=description)
                db.session.add(new_role)
                print(f"  - Added role: '{name}'")
                roles_added_count += 1
            else:
                print(f"  - Role '{name}' already exists.")

        if roles_added_count > 0:
            db.session.commit()
            print(f"Successfully committed {roles_added_count} new role(s).")
        else:
            print("All default roles already present in the database.")
        return True # Indicate success

    except Exception as e:
        db.session.rollback()
        print("ERROR: Failed to seed roles. Database rolled back.")
        print(f"Error details: {e}")
        return False # Indicate failure

if __name__ == '__main__':
    # Create app to get application context
    app = create_app(os.environ.get('FLASK_ENV') or 'development')

    # Run seeding logic within app context to access db
    with app.app_context():
        success = seed_initial_roles()

    # Exit with appropriate status code
    sys.exit(0 if success else 1)