import sys
import os
import argparse
from dotenv import load_dotenv # Import dotenv

# Load environment variables from .env file
load_dotenv()


from app import create_app  # noqa: E402
from app.models import db, User, Role  # noqa: E402

def assign_admin_role(username_to_assign):
    """Finds a user and assigns the Admin role to them."""
    print(f"Attempting to make user '{username_to_assign}' an admin...")

    # Find the Admin role (should have been created by migration)
    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        print("ERROR: 'Admin' role not found in the database.")
        print("Please ensure the migration that creates default roles ran successfully.")
        return False # Indicate failure

    # Find the user by username
    user = User.query.filter_by(username=username_to_assign).first()
    if not user:
        print(f"ERROR: User '{username_to_assign}' not found.")
        return False

    # Check if user already has the role
    if user.has_role('Admin'): # Use the helper method from the User model
        print(f"User '{username_to_assign}' already has the 'Admin' role.")
        return True # Indicate success (already done)

    # Assign the role and commit
    try:
        user.roles.append(admin_role)
        db.session.commit()
        print(f"Successfully assigned 'Admin' role to user '{username_to_assign}'.")
        return True # Indicate success
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: Failed to assign role. Database rolled back. Error: {e}")
        return False # Indicate failure

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Assign the Admin role to a specified user.")
    parser.add_argument("username", help="The username of the user to make admin.")
    args = parser.parse_args()

    # Create app to get application context
    # Uses FLASK_ENV from .env (loaded above) or defaults to 'development'
    app = create_app(os.environ.get('FLASK_ENV') or 'development')

    # Run the assignment logic within the app context
    with app.app_context():
        success = assign_admin_role(args.username)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)

