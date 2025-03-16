from flask import Blueprint, render_template, request, redirect, url_for
from models import Product, db

routes_blueprint = Blueprint("routes", __name__)

# Root Route
@routes_blueprint.route("/")
def product_list():
    products = Product.query.all()
    return render_template("/products/list.html", products=products)


# Add product
@routes_blueprint.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        sku = request.form.get("sku")
        description = request.form.get("description")
        price = request.form.get("price")
        stock_level = request.form.get("stock_level")

        errors ={}

        if not name:
            errors["name"] = "Name is required"
        if not sku:
            errors["sku"] = "SKU is required"
        if not price:
            errors["Price"] = "Price is required"
        else:
            try:
                float(price)
            except ValueError:
                errors["price"] = "Price must be a number"
    
        if not stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            try:
                int(stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"
        
        if errors:
            return render_template("products/add/html", errors=errors)

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
        product.name = request.form.get("name")
        product.sku = request.form.get("sku")
        product.description = request.form.get("description")
        product.price = request.form.get("price")
        product.stock_level = request.form.get("stock_level")

        errors = {}

        if not product.name:
            errors["name"] = "Name is required"
        if not product.sku:
            errors["sku"] = "SKU is required"
        if not product.price:
            errors["price"] = "Price is required"
        else:
            try:
                float(product.price)
            except ValueError:
                errors["price"] = "Price must be a number"
        if not product.stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            try:
                int(product.stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"
        
        if errors:
            return render_template("products/edit.html", product=product, errors=errors)

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


# In-stock 
@routes_blueprint.route("/products/stock/in/<int:product_id>", methods=["GET", "POST"])
def stock_in(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        quantity = int(request.form["quantity"])
        product.stock_level += quantity
        db.session.commit()
        return redirect(url_for("routes.product_list"))
    return render_template("products/stock_in.html", product=product)

# Out-stock
@routes_blueprint.route("/products/stock/out/<int:product_id>", methods=["GET", "POST"])
def stock_out(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        quantity = int(request.form["quantity"])
        if product.stock_level >= quantity:
            product.stock_level -= quantity
            db.session.commit()
        return redirect(url_for("routes.product_list"))
    return render_template("products/stock_out.html", product=product)


@routes_blueprint.route("/stock_levels")
def stock_levels():
    products = Product.query.all()
    return render_template("stock_levels.html", products=products)


    

