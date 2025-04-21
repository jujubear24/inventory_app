from .db import db
from sqlalchemy import Table, Column, Integer, ForeignKey


user_roles = Table('user_roles', db.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__: str = 'role' # Explicit table name

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(80), unique=True, nullable=False)
    description: str = db.Column(db.String(255)) # Optional description

    # Relationship defined via backref from User model
    # users: List['User'] # Defined by backref='roles' in User model

    def __repr__(self) -> str:
        return f'<Role {self.name}>'