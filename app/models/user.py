from .db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone
from typing import Optional
from .role import Role, user_roles

class User(db.Model, UserMixin):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: Optional[str] = db.Column(db.String(128))
    first_name: Optional[str] = db.Column(db.String(64))
    last_name: Optional[str] = db.Column(db.String(64))
    is_active: bool = db.Column(db.Boolean, default=True)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = db.Column(db.DateTime)

    # --- Many-to-many relationship with Role ---
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        backref=db.backref('users', lazy='dynamic'), # Allows accessing role.users
        lazy='dynamic' # Use 'dynamic' if you expect many roles per user or users per role
    )


    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def has_role(self, role_name: str) -> bool:
        """Check if a user has a specific role."""
        return self.roles.filter(Role.name == role_name).count() > 0
    
    @property
    def is_admin(self) -> bool:
        """Check if the user has the 'Admin' role."""
        return self.has_role('Admin')