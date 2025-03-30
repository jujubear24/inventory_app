# app/routes/products.py
from flask import Blueprint, render_template, request, redirect, url_for, Response
from app.models import db, Product
from typing import Dict, List, Union, Optional

products_bp = Blueprint("products", __name__, url_prefix="/products")

@products_bp.route("/add", methods=["GET", "POST"])
def add_product() -> Union[str, Response]:
    if request.method == "POST":
        name: str = request.form.get("name", "")
        sku: str = request.form.get("sku", "")
        description: str = request.form.get("description", "")
        price: str = request.form.get("price", "0")
        stock_level: str = request.form.get("stock_level", "")
        low_stock_threshold: str = request.form.get("low_stock_threshold", "")

        errors: Dict[str, str] = {}

        if not name:
            errors["name"] = "Name is required"
        if not sku:
            errors["sku"] = "SKU is required"
        if not price:
            errors["Price"] = "Price is required"
        else:
            try:
                price_float: float = float(price)
            except ValueError:
                errors["price"] = "Price must be a number"
    
        if not stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            try:
                stock_level_int: int = int(stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"
        
        if not low_stock_threshold:
            errors["low_stock_threshold"] = "Low stock threshold is required"
        else:
            try:
                low_stock_threshold_int: int = int(low_stock_threshold)
            except ValueError:
                errors["low_stock_threshold"] = "Low stock threshold must be an integer"

        if errors:
            return render_template("products/add.html", errors=errors)

        # Convert only after validation
        price_float = float(price)
        stock_level_int = int(stock_level)
        low_stock_threshold_int = int(low_stock_threshold)

        new_product: Product = Product(
            name=name, 
            sku=sku, 
            description=description, 
            price=price_float, 
            stock_level=stock_level_int, 
            low_stock_threshold=low_stock_threshold_int
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("main.product_list"))
    return render_template("products/add.html")

@products_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id: int) -> Union[str, Response]:
    product: Product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form.get("name", "")
        product.sku = request.form.get("sku", "")
        product.description = request.form.get("description", "")
        price: str = request.form.get("price", "")
        stock_level: str = request.form.get("stock_level", "")
        low_stock_threshold: str = request.form.get("low_stock_threshold", "")

        errors: Dict[str, str] = {}

        if not product.name:
            errors["name"] = "Name is required"
        if not product.sku:
            errors["sku"] = "SKU is required"
        
        price_float: Optional[float] = None
        if not price:
            errors["price"] = "Price is required"
        else:
            try:
                price_float = float(price)
            except ValueError:
                errors["price"] = "Price must be a number"
        
        stock_level_int: Optional[int] = None
        if not stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            try:
                stock_level_int = int(stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"

        low_stock_threshold_int: Optional[int] = None
        if not low_stock_threshold:
            errors["low_stock_threshold"] = "Low stock threshold is required"
        else:
            try:
                low_stock_threshold_int = int(low_stock_threshold)
            except ValueError:
                errors["low_stock_threshold"] = "Low stock threshold must be an integer"
        
        if errors:
            return render_template("products/edit.html", product=product, errors=errors)

        # Only update if validation passed
        if price_float is not None:
            product.price = price_float
        if stock_level_int is not None:
            product.stock_level = stock_level_int
        if low_stock_threshold_int is not None:
            product.low_stock_threshold = low_stock_threshold_int

        db.session.commit()
        return redirect(url_for("main.product_list"))
    
    return render_template("products/edit.html", product=product)

@products_bp.route("/delete/<int:product_id>")
def delete_product(product_id: int) -> Response:
    product: Product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("main.product_list"))

@products_bp.route("/stock/in/<int:product_id>", methods=["GET", "POST"])
def stock_in(product_id: int) -> Union[str, Response]:
    product: Product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        quantity: int = int(request.form["quantity"])
        product.stock_level += quantity
        db.session.commit()
        return redirect(url_for("main.product_list"))
    return render_template("products/stock_in.html", product=product)

@products_bp.route("/stock/out/<int:product_id>", methods=["GET", "POST"])
def stock_out(product_id: int) -> Union[str, Response]:
    product: Product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        quantity: int = int(request.form["quantity"])
        if product.stock_level >= quantity:
            product.stock_level -= quantity
            db.session.commit()
        return redirect(url_for("main.product_list"))
    return render_template("products/stock_out.html", product=product)


