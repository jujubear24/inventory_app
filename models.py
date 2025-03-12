from flask_sqlalchemy import SQLAlchemy # type: ignore

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock_level = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Product {self.name}>'