from typing import Dict, Any, Optional, List, Tuple, cast
from app.models.db import db
from app.models.user import User

class UserService:
    @staticmethod
    def get_all_users() -> List[User]:
        """Get all users."""
        return User.query.all()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return db.session.get(User, user_id)  # Using newer API as recommended
    
    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Tuple[Optional[User], Dict[str, str]]:
        """Create a new user with validation."""
        errors: Dict[str, str] = UserService.validate_user_data(user_data)
        if errors:
            return None, errors
        
        user: User = User(
            username=user_data.get('username', ''),
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_admin=user_data.get('is_admin', False)
        )
        user.set_password(cast(str, user_data.get('password', '')))
        
        db.session.add(user)
        db.session.commit()
        return user, {}
    
    @staticmethod
    def update_user(user_id: int, user_data: Dict[str, Any]) -> Tuple[Optional[User], Dict[str, str]]:
        """Update a user."""
        user: Optional[User] = db.session.get(User, user_id)
        if not user:
            return None, {'error': 'User not found'}
        
        errors: Dict[str, str] = {}
        
        if 'username' in user_data and user_data['username'] != user.username:
            username_exists: Optional[User] = User.query.filter_by(username=user_data['username']).first()
            if username_exists:
                errors['username'] = 'Username already taken'
            else:
                user.username = cast(str, user_data['username'])
        
        if 'email' in user_data and user_data['email'] != user.email:
            email_exists: Optional[User] = User.query.filter_by(email=user_data['email']).first()
            if email_exists:
                errors['email'] = 'Email already registered'
            else:
                user.email = cast(str, user_data['email'])
        
        if errors:
            return None, errors
        
        if 'first_name' in user_data:
            user.first_name = cast(str, user_data['first_name'])
        
        if 'last_name' in user_data:
            user.last_name = cast(str, user_data['last_name'])
        
        if 'is_admin' in user_data:
            user.is_admin = bool(user_data['is_admin'])
        
        if 'password' in user_data and user_data['password']:
            user.set_password(cast(str, user_data['password']))
        
        db.session.commit()
        return user, {}
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Delete a user."""
        user: Optional[User] = db.session.get(User, user_id)
        if not user:
            return False
        
        db.session.delete(user)
        db.session.commit()
        return True
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any]) -> Dict[str, str]:
        """Validate user data and return errors."""
        errors: Dict[str, str] = {}
        
        if not data.get('username'):
            errors['username'] = "Username is required"
        elif User.query.filter_by(username=data['username']).first():
            errors['username'] = "Username already taken"
        
        if not data.get('email'):
            errors['email'] = "Email is required"
        elif User.query.filter_by(email=data['email']).first():
            errors['email'] = "Email already registered"
        
        if not data.get('password'):
            errors['password'] = "Password is required"
        elif len(str(data.get('password', ''))) < 8:
            errors['password'] = "Password must be at least 8 characters"
        
        return errors