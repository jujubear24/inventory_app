from .db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone
from typing import Optional
from .role import Role, user_roles
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer 



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

    def has_permission(self, permission_name: str) -> bool:
        """Check if the user has a specific permission through any of their roles."""
        if self.has_role('Admin'):
            return True

        for role in self.roles:
            if role.has_permission(permission_name):
                return True

        return False

    # --- Password Reset Token Methods ---
    def get_reset_password_token(self, expires_sec: int = 1800) -> Optional[str]:
        """
        Generates a password reset token.
        Args:
            expires_sec: Token expiration time in seconds. Default is 1800 (30 minutes).
        Returns:
            The generated token string, or None if SECRET_KEY is not set.
        """
        secret_key = current_app.config.get("SECRET_KEY")
        if not secret_key:
            current_app.logger.error(
                "SECRET_KEY not set. Cannot generate password reset token."
            )
            return None

        s = Serializer(secret_key)
        try:
            return s.dumps({"user_id": self.id})
        except Exception as e:
            current_app.logger.error(f"Error generating token for user {self.id}: {e}")
            return None

    @staticmethod
    def verify_reset_password_token(
        token: str, max_age_sec: int = 1800
    ) -> Optional["User"]:
        """
        Verifies a password reset token and returns the user if valid.
        Args:
            token: The token string to verify.
            max_age_sec: Maximum age of the token in seconds. Default is 1800 (30 minutes).
        Returns:
            The User object if the token is valid, otherwise None.
        """
        secret_key = current_app.config.get("SECRET_KEY")
        if not secret_key:
            current_app.logger.error(
                "SECRET_KEY not set. Cannot verify password reset token."
            )
            return None

        s = Serializer(secret_key)
        try:
            data = s.loads(token, max_age=max_age_sec)
            user_id = data.get("user_id")
            if user_id is None:
                current_app.logger.warning("Token is missing user_id.")
                return None
        except Exception as e:  # Catches expired signature, bad signature, etc.
            current_app.logger.warning(f"Password reset token verification failed: {e}")
            return None

        return User.query.get(user_id)
