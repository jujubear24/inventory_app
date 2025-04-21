from .db import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from typing import Optional, List
from .role import Role, user_roles

class User(db.Model, UserMixin):
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email: str = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(128))
    first_name: Optional[str] = db.Column(db.String(64))
    last_name: Optional[str] = db.Column(db.String(64))
    is_admin: bool = db.Column(db.Boolean, default=False)
    is_active: bool = db.Column(db.Boolean, default=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    last_login: Optional[datetime] = db.Column(db.DateTime)
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username

