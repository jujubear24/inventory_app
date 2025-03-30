# app/routes/products.py
from flask import Blueprint, render_template, request, redirect, url_for, Response
from app.models import db, Product
from app.utils import validate_product_data, generate_sku
from typing import  Union

products_bp = Blueprint("products", __name__, url_prefix="/products")

@products_bp.route("/add", methods=["GET", "POST"])
def add_product() -> Union[str, Response]:
    if request.method == "POST":
        # Collect form data into a dictionary
        product_data = {
            "name": request.form.get("name", ""),
            "sku": request.form.get("sku", ""),
            "description": request.form.get("description", ""),
            "price": request.form.get("price", "0"),
            "stock_level": request.form.get("stock_level", ""),
            "low_stock_threshold": request.form.get("low_stock_threshold", "")
        }

        # Generate SKU if not provided
        if not product_data["sku"]:
            product_data["sku"] = generate_sku(product_data["name"])

        # Validate data
        errors = validate_product_data(product_data)
        
        if errors:
            return render_template("products/add.html", errors=errors)

        # Convert to appropriate types after validation
        new_product: Product = Product(
            name=product_data["name"], 
            sku=product_data["sku"], 
            description=product_data["description"], 
            price=float(product_data["price"]), 
            stock_level=int(product_data["stock_level"]), 
            low_stock_threshold=int(product_data["low_stock_threshold"])
        )
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("main.product_list"))
    return render_template("products/add.html")

@products_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id: int) -> Union[str, Response]:
    product: Product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        # Collect form data into a dictionary
        product_data = {
            "name": request.form.get("name", ""),
            "sku": request.form.get("sku", ""),
            "description": request.form.get("description", ""),
            "price": request.form.get("price", ""),
            "stock_level": request.form.get("stock_level", ""),
            "low_stock_threshold": request.form.get("low_stock_threshold", "")
        }

        # Validate data
        errors = validate_product_data(product_data)
        
        if errors:
            return render_template("products/edit.html", product=product, errors=errors)

        # Update product with validated data
        product.name = product_data["name"]
        product.sku = product_data["sku"]
        product.description = product_data["description"]
        product.price = float(product_data["price"])
        product.stock_level = int(product_data["stock_level"])
        product.low_stock_threshold = int(product_data["low_stock_threshold"])

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
        try:
            quantity: int = int(request.form["quantity"])
            if quantity > 0:
                product.stock_level += quantity
                db.session.commit()
        except (ValueError, KeyError):
            # Handle invalid input gracefully
            pass
        return redirect(url_for("main.product_list"))
    return render_template("products/stock_in.html", product=product)

@products_bp.route("/stock/out/<int:product_id>", methods=["GET", "POST"])
def stock_out(product_id: int) -> Union[str, Response]:
    product: Product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        try:
            quantity: int = int(request.form["quantity"])
            if quantity > 0 and product.stock_level >= quantity:
                product.stock_level -= quantity
                db.session.commit()
        except (ValueError, KeyError):
            # Handle invalid input gracefully
            pass
        return redirect(url_for("main.product_list"))
    return render_template("products/stock_out.html", product=product)




