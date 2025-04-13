from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.models import db, Product
from app.forms.product import ProductForm, ConfirmDeleteForm
from app.utils import generate_sku
from typing import Union
from sqlalchemy.exc import IntegrityError

# Initialize Product Blueprint
products_bp = Blueprint("products", __name__, url_prefix="/products")

# Route: Add Product
@products_bp.route("/add", methods=["GET", "POST"])
def add_product() -> Union[str, Response]:
    form = ProductForm()
    form.submit.label.text = 'Add Product'

    if form.validate_on_submit():
    
        sku = form.sku.data
        new_product_name = form.name.data


        if not sku:
            sku = generate_sku(new_product_name)
        elif Product.query.filter_by(sku=sku).first():
            form.sku.errors.append("SKU already exists. Leave blank to auto-generate or enter a unique one.")
            return render_template("products/add.html", form=form, title="Add New Product")

        new_product = Product(
            name=new_product_name,
            sku=sku,
            description=form.description.data,
            price=form.price.data, # WTForms handles float conversion
            stock_level=form.stock_level.data, # WTForms handles int conversion
            low_stock_threshold=form.low_stock_threshold.data
        )
        try:
            db.session.add(new_product)
            db.session.commit()
            flash(f'Product "{new_product.name}" added successfully!', 'success')
            return redirect(url_for("main.product_list"))
        
        except IntegrityError as e:
            db.session.rollback()
            error_info = str(e.orig).lower()

            if 'unique constraint' in error_info and 'product.sku' in error_info:
                 flash(f'Error adding product: The generated or provided SKU \'{sku}\' already exists. Please try adding again or use a different manual SKU.', 'danger')
                 form.sku.data = '' # Clear potentially problematic auto-generated SKU
            else:
                flash(f'Database error adding product: {str(e)}', 'danger')

        # Catch other potential exceptions during commit
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    
    return render_template("products/add.html", form=form, title="Add New Product")


# Route: Edit product
@products_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id: int) -> Union[str, Response]:
    product = db.session.get(Product, product_id) 
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.product_list'))

    # Pre-populate form with product data on GET
    form = ProductForm(obj=product)
    form.submit.label.text = 'Update Product' # Customize button label

    if form.validate_on_submit():
        # Check if SKU is being changed and if the new one conflicts
        new_sku = form.sku.data
        if new_sku != product.sku and Product.query.filter(Product.id != product_id, Product.sku == new_sku).first():
             form.sku.errors.append("This SKU is already used by another product.")
             # Rerender form with error
             return render_template("products/edit.html", form=form, title=f"Edit Product: {product.name}", product_id=product_id)
        else:
            # Populate object attributes from form data
            form.populate_obj(product)
            try:
                db.session.commit()
                flash(f'Product "{product.name}" updated successfully!', 'success')
                return redirect(url_for("main.product_list"))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating product: {str(e)}', 'danger')

    # For GET request or validation failure
    return render_template("products/edit.html", form=form, title=f"Edit Product: {product.name}", product_id=product_id) # Pass product_id for potential actions

# Route: Delete product
@products_bp.route("/delete/<int:product_id>", methods=["GET", "POST"]) 
def delete_product(product_id: int) -> Union[str, Response]:
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for("main.product_list"))

    form = ConfirmDeleteForm() # Instantiate the confirmation form

    if form.validate_on_submit():
      
        try:
            product_name = product.name # Store name before deleting
            db.session.delete(product)
            db.session.commit()
            flash(f'Product "{product_name}" deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting product: {str(e)}', 'danger')
        return redirect(url_for("main.product_list"))

    # GET request - Show confirmation page
    return render_template("products/delete_confirm.html",
                           product=product,
                           form=form,
                           title=f"Confirm Deletion: {product.name}")


# Route: Stock-in
@products_bp.route("/stock/in/<int:product_id>", methods=["GET", "POST"])
def stock_in(product_id: int) -> Union[str, Response]:
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.product_list'))

    if request.method == "POST":
        try:
            quantity: int = int(request.form["quantity"])
            if quantity > 0:
                product.stock_level += quantity
                db.session.commit()
                flash(f'{quantity} units added to stock for "{product.name}".', 'success')
            else:
                flash('Please enter a positive quantity.', 'warning')
        except (ValueError, KeyError):
            flash('Invalid quantity entered.', 'danger')
        except Exception as e:
             db.session.rollback()
             flash(f'Error updating stock: {str(e)}', 'danger')
        # Redirect to list or back to stock_in page? Redirecting to list for now.
        return redirect(url_for("main.product_list"))

    return render_template("products/stock_in.html", product=product)

# Route: Stock-out
@products_bp.route("/stock/out/<int:product_id>", methods=["GET", "POST"])
def stock_out(product_id: int) -> Union[str, Response]:
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.product_list'))

    if request.method == "POST":
        try:
            quantity: int = int(request.form["quantity"])
            if quantity <= 0:
                 flash('Please enter a positive quantity.', 'warning')
            elif product.stock_level >= quantity:
                product.stock_level -= quantity
                db.session.commit()
                flash(f'{quantity} units removed from stock for "{product.name}".', 'success')
            else:
                flash(f'Cannot remove {quantity} units. Only {product.stock_level} in stock.', 'warning')
        except (ValueError, KeyError):
            flash('Invalid quantity entered.', 'danger')
        except Exception as e:
             db.session.rollback()
             flash(f'Error updating stock: {str(e)}', 'danger')
        # Redirect to list or back to stock_out page? Redirecting to list for now.
        return redirect(url_for("main.product_list"))

    return render_template("products/stock_out.html", product=product)



