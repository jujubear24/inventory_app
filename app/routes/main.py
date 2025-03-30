# app/routes/main.py
from flask import Blueprint, render_template
from app.models import Product
from typing import List

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def product_list() -> str:
    products: List[Product] = Product.query.all()
    return render_template("/products/list.html", products=products)

@main_bp.route("/inventory_status")
def inventory_status() -> str:
    products: List[Product] = Product.query.all()
    return render_template("inventory_status.html", products=products)

