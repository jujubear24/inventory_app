import sys
import os
from dotenv import load_dotenv

# Load .env 
load_dotenv()

from app import create_app # noqa: E402
from app.models import db, Role, Permission   # noqa: E402

# --- Application Permissions ---

APP_PERMISSIONS = {
    'view_dashboard': 'Allow viewing the main dashboard',
    'view_products': 'Allow viewing product list and details',
    'add_products': 'Allow adding new products',
    'edit_products': 'Allow editing existing products',
    'delete_products': 'Allow deleting products',
    'manage_stock': 'Allow adjusting stock levels (stock in/out)',
    'view_reports': 'Allow viewing inventory reports',
    'manage_users': 'Allow managing users (add/edit/delete/assign roles)',
    'view_users': 'Allow viewing the user list',
}

# --- Define Permissions per Role ---
ROLE_PERMISSIONS = {
    'Admin': list(APP_PERMISSIONS.keys()), # Give Admin all defined permissions
    'User': [ # User: basic viewing permissions
        'view_dashboard',
        'view_products',
    ]
}


def seed_permissions_and_assignments():
    """Creates permissions if they don't exist and assigns them to roles."""

    print("Seeding permissions and assigning to roles...")
    permissions_added_count = 0
    assignments_added_count = 0

    # 1. Create Permissions if they don't exist
    print("Checking/Creating Permissions...")
    permission_objects = {}
    try:
        for name, description in APP_PERMISSIONS.items():
            perm = Permission.query.filter_by(name=name).first()
            if not perm:
                perm = Permission(name=name, description=description)
                db.session.add(perm)
                print(f"  - Adding permission: '{name}'")
                permissions_added_count += 1
            else:
                print(f"  - Permission '{name}' already exists.")
            permission_objects[name] = perm # Store object for assignment phase

        if permissions_added_count > 0:
            db.session.commit() # Commit newly added permissions
            print(f"Committed {permissions_added_count} new permission(s).")
        else:
            print("All defined permissions already exist.")

    except Exception as e:
        db.session.rollback()
        print(f"\nERROR creating permissions: {e}")
        return False # Stop if permissions can't be created

    # 2. Assign Permissions to Roles
    print("\nChecking/Assigning Permissions to Roles...")
    try:
        for role_name, permission_names in ROLE_PERMISSIONS.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                print(f"  - WARNING: Role '{role_name}' not found. Skipping assignments.")
                continue

            print(f"  - Processing role: '{role_name}'")
            for perm_name in permission_names:
                if perm_name not in permission_objects:
                    print(f"    - WARNING: Permission '{perm_name}' defined in ROLE_PERMISSIONS but not found in APP_PERMISSIONS or database. Skipping.")
                    continue

                permission = permission_objects[perm_name]
                # Check if role already has permission before adding
                if not role.has_permission(perm_name):
                    role.permissions.append(permission)
                    print(f"    - Assigning permission '{perm_name}' to role '{role_name}'.")
                    assignments_added_count += 1
                else: 
                   print(f"    - Role '{role_name}' already has permission '{perm_name}'.")

        if assignments_added_count > 0:
            db.session.commit() # Commit role-permission assignments
            print(f"Committed {assignments_added_count} new role-permission assignment(s).")
        else:
            print("All defined role-permission assignments already exist.")

        print("\nSeeding finished successfully.")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"\nERROR assigning permissions to roles: {e}")
        return False

if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV') or 'development')
    with app.app_context():
        success = seed_permissions_and_assignments()

    sys.exit(0 if success else 1)

