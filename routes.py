from flask import Blueprint, render_template
from models import Product

routes_blueprint = Blueprint("routes", __name__)

@routes_blueprint.route("/")
def product_list():
    products = Product.query.all()
    return render_template("product/list.html", products=products)

