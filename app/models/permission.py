from .db import db
from sqlalchemy import Table, Column, Integer, ForeignKey

# --- Association Table for Role
role_permissions = Table('role_permissions', db.metadata,
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id'), primary_key=True)
)


class Permission(db.Model):
    __tablename__: str = 'permission'

    id: int = db.Column(db.Integer, primary_key=True)

    # Name of the permission (e.g., 'edit_users', 'view_reports')
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    description: str = db.Column(db.String(255)) # Optional 

    # Relationship defined via backref from Role model
    # roles: List['Role'] # Defined by backref='permissions' in Role model

    def __repr__(self) -> str:
        return f'<Permission {self.name}>'
    

