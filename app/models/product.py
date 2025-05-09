from app.models.db import db
from typing import Any
from sqlalchemy.types import Numeric 

class Product(db.Model):
    __tablename__: str = 'product'
    
    id: Any = db.Column(db.Integer, primary_key=True)
    name: Any = db.Column(db.String(100), nullable=False, index=True)
    sku: Any = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description: Any = db.Column(db.Text)
    price: Any = db.Column(Numeric(precision=10, scale=2), nullable=False)
    stock_level: Any = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold: Any = db.Column(db.Integer, default=10, nullable=False)
    
    def __repr__(self) -> str:
        return f'<Product {self.name}>'
