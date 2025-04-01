# app/routes/reports.py
from flask import Blueprint, render_template
from app.models import Product
from typing import List
from app.utils import format_currency


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route('/low_stock')
def low_stock_report() -> str:
    low_stock_products: List[Product] = Product.query.filter(
        Product.stock_level <= Product.low_stock_threshold
    ).all()
    return render_template('reports/low_stock.html', products=low_stock_products)

@reports_bp.route('/product_summary')
def product_summary_report() -> str:
    products: List[Product] = Product.query.order_by(Product.name).all()
    return render_template('reports/product_summary.html', products=products)

@reports_bp.route('/product_value')
def product_value_report() -> str:
    products: List[Product] = Product.query.all()
    total_value = sum(product.price * product.stock_level for product in products)
    formatted_value = format_currency(total_value)
    return render_template('reports/product_value.html', products=products, total_value=total_value, formatted_value=formatted_value)

