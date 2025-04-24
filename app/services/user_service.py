from typing import Dict, Any, Optional, List, Tuple, cast
from flask import current_app
from app.models.db import db
from app.models.user import User
from app.models.oauth import OAuth 


class UserService:
    @staticmethod
    def get_all_users() -> List[User]:
        """Get all users."""
        return User.query.order_by(User.username).all()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return db.session.get(User, user_id)
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Tuple[Optional[User], Dict[str, str]]:
        """Create a new user with validation and role assignment"""
        errors: Dict[str, str] = UserService.validate_user_data(user_data, is_new=True)
        if errors:
            return None, errors
        
        user: User = User(
            username=user_data.get('username', ''),
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
        )
        user.set_password(cast(str, user_data.get('password', '')))

        # --- Assign Roles ---
        selected_roles = user_data.get('roles', [])
        user.roles = selected_roles

        try:
            db.session.add(user)
            db.session.commit()
            return user, {}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving new user: {e}", exc_info=True)
            return None, {'database': f'Error saving user: {str(e)}'}
    
    @staticmethod
    def update_user(user_id: int, user_data: Dict[str, Any]) -> Tuple[Optional[User], Dict[str, str]]:
        """Update a user, including roles"""
        user: Optional[User] = db.session.get(User, user_id)
        if not user:
            return None, {'error': 'User not found'}
        
        errors: Dict[str, str] = UserService.validate_user_data(user_data, user_id=user_id, is_new=False)
        if errors:
            return None, errors
        
        # Update standard fields
        if 'username' in user_data:
            user.username = cast(str, user_data['username'])
        if 'email' in user_data:
            user.email = cast(str, user_data['email'])
        if 'first_name' in user_data:
            user.first_name = cast(str, user_data['first_name'])
        if 'last_name' in user_data:
            user.last_name = cast(str, user_data['last_name'])

        # Update password only if provided
        if 'password' in user_data and user_data['password']:
            user.set_password(cast(str, user_data['password']))
        
        # Update roles
        if 'roles' in user_data:
            user.roles = user_data['roles']
        
        try:
            db.session.commit()
            return user, {}
        except Exception as e:
            db.session.rollback()
            # Consider logging the exception e
            return None, {'database': f"Error updating user: {str(e)}"}
        
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Delete a user."""
        user: Optional[User] = db.session.get(User, user_id)
        if not user:
            current_app.logger.warning(f"Attempted to delete non-existent user with ID: {user_id}")
            return False
        
        try:
            #  from app.models.oauth import OAuth
            # OAuth.query.filter_by(user_id=user_id).delete()
            # db.session.flush() # Process deletes before deleting user
            # Need to handle related entities if necessary (e.g., OAuth entries)
            OAuth.query.filter_by(user_id=user_id).delete()
            db.session.flush() 


            db.session.delete(user)
            db.session.commit()
            current_app.logger.info(f"Successfully deleted user with ID: {user_id}") 
            return True
        except Exception:
            db.session.rollback()
            current_app.logger.error(
                f"Error deleting user with ID: {user_id}. Session rolled back.",
                exc_info=True 
            )
            return False
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any], user_id: Optional[int] = None, is_new: bool = True) -> Dict[str, str]:
        """Validate user data and return errors."""
        errors: Dict[str, str] = {}
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username:
            errors['username'] = "Username is required"
        else:
            query = User.query.filter(User.username.ilike(username))
            if user_id: # If updating, exclude the current user
                query = query.filter(User.id != user_id)
            if query.first():
                errors['username'] = "Username already taken"
        
        if not email:
            errors['email'] = "Email is required"
        else:
            query = User.query.filter(User.email.ilike(email))
            if user_id: # If updating, exclude the current user
                query = query.filter(User.id != user_id)
            if query.first():
                errors['email'] = "Email already registered"
        
        if is_new and not password:
            errors['password'] = "Password is required"
        if password and len(password) < 8:
             errors['password'] = "Password must be at least 8 characters"
        
        return errors 
