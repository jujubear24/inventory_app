from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.models import db, Product
from app.services.product_service import ProductService
from app.forms.product import ProductForm, ConfirmDeleteForm
from typing import Union


# Initialize Product Blueprint
products_bp = Blueprint("products", __name__, url_prefix="/products")

# Route: Add Product
@products_bp.route("/add", methods=["GET", "POST"])
def add_product() -> Union[str, Response]:
    form = ProductForm()
    if form.validate_on_submit():
        # Pass form data to the service
        product, errors = ProductService.create_product(form.data)
        if product:
            flash('Product added successfully!', 'success')
            return redirect(url_for('main.product_list')) # Or wherever you list products
        else:
            # Display validation/database errors from the service
            for field, error_msg in errors.items():
                if field.startswith('_'): # Handle general errors
                     flash(f"Error: {error_msg}", 'danger')
                elif hasattr(form, field): # Assign error to specific form field
                     getattr(form, field).errors.append(error_msg)
                else: # Fallback for unexpected errors
                     flash(f"Error with {field}: {error_msg}", 'danger')
    # If GET request or form validation failed
    return render_template('products/add.html', title='Add Product', form=form)


# Route: Edit product
@products_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id: int) -> Union[str, Response]:
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('main.product_list'))

    form = ProductForm(obj=product) # Pre-populate form on GET

    if form.validate_on_submit():
        # Pass form data and ID to the update service method
        updated_product, errors = ProductService.update_product(product_id, form.data)
        if updated_product:
            flash('Product updated successfully!', 'success')
            return redirect(url_for('main.product_list'))
        else:
             # Display errors similar to add_product
             for field, error_msg in errors.items():
                 # ... (error handling logic) ...
                 flash(f"Update failed: {error_msg}", 'danger')

    # If GET request or POST validation failed
    return render_template('edit_product.html', title='Edit Product', form=form, product=product)


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



