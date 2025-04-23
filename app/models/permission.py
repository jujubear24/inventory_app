from .db import db

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
    

