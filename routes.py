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
        price = request.form.get("price", "0")
        stock_level = request.form.get("stock_level")
        low_stock_threshold = request.form.get("low_stock_threshold")

        errors ={}

        if not name:
            errors["name"] = "Name is required"
        if not sku:
            errors["sku"] = "SKU is required"
        if not price:
            errors["Price"] = "Price is required"
        else:
            try:
                price = float(price)
            except ValueError:
                errors["price"] = "Price must be a number"
    
        if not stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            try:
                stock_level = int(stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"
        
        if not low_stock_threshold:
            errors["low_stock_threshold"] = "Low stock threshold is required"
        else:
            try:
                low_stock_threshold = int(low_stock_threshold)
            except ValueError:
                errors["low_stock_threshold"] = "Low stock threshold must be an integer"

        if errors:
            # Fixed the template path (was "products/add/html")
            return render_template("products/add.html", errors=errors)

        new_product = Product(name=name, sku=sku, description=description, price=price, stock_level=stock_level, low_stock_threshold=low_stock_threshold)
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
        price = request.form.get("price")
        stock_level = request.form.get("stock_level")
        low_stock_threshold = request.form.get("low_stock_threshold")

        errors = {}

        if not product.name:
            errors["name"] = "Name is required"
        if not product.sku:
            errors["sku"] = "SKU is required"
        if not price:
            errors["price"] = "Price is required"
        else:
            # Fixed: Don't set price=0 before trying to convert
            try:
                price = float(price)
            except ValueError:
                errors["price"] = "Price must be a number"
        
        if not stock_level:
            errors["stock_level"] = "Stock level is required"
        else:
            # Fixed: Don't set stock_level=0 before trying to convert
            try:
                stock_level = int(stock_level)
            except ValueError:
                errors["stock_level"] = "Stock level must be an integer"

        if not low_stock_threshold:
            errors["low_stock_threshold"] = "Low stock threshold is required"
        else:
            # Fixed: Don't set low_stock_threshold=0 before trying to convert
            try:
                low_stock_threshold = int(low_stock_threshold)
            except ValueError:
                errors["low_stock_threshold"] = "Low stock threshold must be an integer"
        
        if errors:
            return render_template("products/edit.html", product=product, errors=errors)

        product.price = price
        product.stock_level = stock_level
        product.low_stock_threshold = low_stock_threshold

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

@routes_blueprint.route("/reports/stock_level")
def stock_level_report():
    products = Product.query.order_by(Product.name).all()
    return render_template("reports/stock_level.html", products=products)

@routes_blueprint.route('/reports/low_stock')
def low_stock_report():
    # This will work once all values are properly stored as integers
    low_stock_products = Product.query.filter(Product.stock_level <= Product.low_stock_threshold).all()
    return render_template('reports/low_stock.html', products=low_stock_products)

@routes_blueprint.route('/reports/product_summary')
def product_summary_report():
    products = Product.query.order_by(Product.name).all()
    return render_template('reports/product_summary.html', products=products)

@routes_blueprint.route('/reports/product_value')
def product_value_report():
    products = Product.query.all()
    total_value = sum(product.price * product.stock_level for product in products)
    return render_template('reports/product_value.html', products=products, total_value=total_value)


