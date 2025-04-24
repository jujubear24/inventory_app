from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from flask_login import login_required, current_user
from app.services.user_service import UserService
from app.forms.user import UserForm, UserEditForm
from app.models.user import User
from functools import wraps
from typing import Callable, Any, Dict, Optional, Union, cast, TypeVar, List

# Define a generic type variable for the decorator
F = TypeVar('F', bound=Callable[..., Any])

admin_bp: Blueprint = Blueprint('admin', __name__, url_prefix='/admin')


# Permission required decorator
def permission_required(permission_name: str) -> Callable:
    """Decorator to check if the current user has the required permission."""

    def decorator(f: F) -> F:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # 1. Check if user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))

            # 2. Check if user has the required permission
            if not current_user.has_permission(permission_name):
                flash(f'You do not have permission to access this resource ({permission_name}).', 'danger')
                # Redirect to a more appropriate page, like the dashboard
                return redirect(url_for('main.product_list'))

            # 3. User is authenticated and has permission
            return f(*args, **kwargs)
        return cast(F, decorated_function)
    return decorator



@admin_bp.route('/users')
@login_required
@permission_required('view_users')
def user_list() -> str:
    users: List[User] = UserService.get_all_users()
    return render_template('admin/users/list.html', users=users, title="User Management")

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def add_user() -> Union[str, Response]:
    form: UserForm = UserForm()
    if form.validate_on_submit():
        user_data: Dict[str, Any] = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'roles': form.roles.data
        }
        user, errors = UserService.create_user(user_data)
        if errors:
            for field, error_list in errors.items():
                 # If error is general (like 'database'), flash it
                 if field == 'database' or not hasattr(form, field):
                     flash(f"Error creating user: {error_list}", 'danger')
                 # Otherwise, add error to the specific form field
                 else:
                     # WTForms errors is a list
                     if isinstance(error_list, list):
                          for error in error_list:
                              getattr(form, field).errors.append(error)
                     else: # If service returned a single string
                          getattr(form, field).errors.append(error_list)
            
        else:
            flash(f'User "{user.username}" created successfully!', 'success')
            return redirect(url_for('admin.user_list'))
    
    return render_template('admin/users/add.html', form=form, title="Add New User")

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def edit_user(user_id: int) -> Union[str, Response]:
    user: Optional[User] = UserService.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.user_list'))
    
    form: UserEditForm = UserEditForm(obj=user)

    if request.method == 'GET':
        form.roles.data = user.roles


    if form.validate_on_submit():
        user_data: Dict[str, Any] = {
            'username': form.username.data,
            'email': form.email.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'roles': form.roles.data
        }
        if form.password.data:
            user_data['password'] = form.password.data
        
        updated_user, errors = UserService.update_user(user_id, user_data)
        if errors:
            for field, error_list in errors.items():
                if field == 'database' or field == 'error' or not hasattr(form, field):
                    flash(f"Error updating user: {error_list}", 'danger')
                else:
                    if isinstance(error_list, list):
                        for error in error_list:
                              getattr(form, field).errors.append(error)
                    else:
                        getattr(form, field).errors.append(error_list)
        else:
            flash(f'User "{updated_user.username}" updated successfully!', 'success')
            return redirect(url_for('admin.user_list'))
    
    return render_template('admin/users/edit.html', form=form, user=user, title=f"Edit User: {user.username}")

# --- delete_user route remains the same ---
@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@permission_required('manage_users')
def delete_user(user_id: int) -> Response:
    if current_user.id == user_id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.user_list'))
    
    if UserService.delete_user(user_id):
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found. or error deleting user.', 'danger')
    
    return redirect(url_for('admin.user_list'))
