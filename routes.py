from flask import Blueprint, render_template, request, redirect, url_for
from models import Product, db

routes_blueprint = Blueprint("routes", __name__)

# Root Route
@routes_blueprint.route("/")
def product_list():
    products = Product.query.all()
    return render_template("products/list.html", products=products)


# Add product
@routes_blueprint.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        sku = request.form["sku"]
        description = request.form["description"]
        price = request.form["price"]
        stock_level = request.form["stock_level"]

        new_product = Product(name=name, sku=sku, description=description, price=price, stock_level=stock_level)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("routes.product_list"))
    return render_template("products/add.html")

# Edit Product
@routes_blueprint.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.sku = request.form["sku"]
        product.description = request.form["description"]
        product.price = request.form["price"]
        product.stock_level = request.form["stock_level"]

        db.session.commit()
        return redirect(url_for("routes.product_list"))
    
    return render_template("products/edit.html", product=product)

# Delete product
@routes_blueprint.route("/products/delete/<int:product_id>")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("routes.product_list"))




