from typing import List, Optional, Tuple
from app.models import db, Role, Permission
from flask import current_app

class RoleService:
    @staticmethod
    def get_all_roles() -> List[Role]:
        """Get all roles ordered by name."""
        try:
            return Role.query.order_by(Role.name).all()
        except Exception as e:
            current_app.logger.error(f"Error fetching all roles: {e}", exc_info=True)
            return []

    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """Get a single role by its ID."""
        try:
            return db.session.get(Role, role_id)
        except Exception as e:
            current_app.logger.error(f"Error fetching role ID {role_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def update_role_permissions(role_id: int, permission_ids: List[int]) -> Tuple[Optional[Role], Optional[str]]:
        """
        Update the permissions associated with a specific role.
        Replaces existing permissions with the provided list.
        """
        role = RoleService.get_role_by_id(role_id)
        if not role:
            return None, "Role not found."

        try:
            # Find the actual Permission objects based on the IDs submitted from the form
            selected_permissions = []
            if permission_ids: # Handle empty list case
                selected_permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()

                # Optional: Verify all submitted IDs correspond to actual permissions
                if len(selected_permissions) != len(permission_ids):
                     current_app.logger.warning(f"Some permission IDs submitted for role {role_id} were invalid.")
                     # Depending on requirements, you might return an error here
                     # return role, "Invalid permission ID submitted."

            # Directly assign the list of Permission objects to the relationship.
            role.permissions = selected_permissions
            db.session.commit()
            current_app.logger.info(f"Updated permissions for role ID {role_id} ('{role.name}')")
            return role, None # Return updated role and no error
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating permissions for role ID {role_id}: {e}", exc_info=True)
            return role, ("Database error updating permissions.")
