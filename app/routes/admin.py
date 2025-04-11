from flask import Blueprint, render_template, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.services.user_service import UserService
from app.forms.user import UserForm, UserEditForm
from app.models.user import User
from functools import wraps
from typing import Callable, Any, Dict, Optional, Union, cast, TypeVar, List

# Define a generic type variable for the decorator
F = TypeVar('F', bound=Callable[..., Any])

admin_bp: Blueprint = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f: F) -> F:
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('main.product_list'))
        return f(*args, **kwargs)
    return cast(F, decorated_function)

@admin_bp.route('/users')
@login_required
@admin_required
def user_list() -> str:
    users: List[User] = UserService.get_all_users()
    return render_template('admin/users/list.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user() -> Union[str, Response]:
    form: UserForm = UserForm()
    if form.validate_on_submit():
        user_data: Dict[str, Any] = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'is_admin': form.is_admin.data
        }
        user, errors = UserService.create_user(user_data)
        if errors:
            for field, error in errors.items():
                if hasattr(form, field):
                    getattr(form, field).errors.append(error)
        else:
            flash('User created successfully!', 'success')
            return redirect(url_for('admin.user_list'))
    
    return render_template('admin/users/add.html', form=form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id: int) -> Union[str, Response]:
    user: Optional[User] = UserService.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.user_list'))
    
    form: UserEditForm = UserEditForm(obj=user)
    if form.validate_on_submit():
        user_data: Dict[str, Any] = {
            'username': form.username.data,
            'email': form.email.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'is_admin': form.is_admin.data
        }
        if form.password.data:
            user_data['password'] = form.password.data
        
        updated_user, errors = UserService.update_user(user_id, user_data)
        if errors:
            for field, error in errors.items():
                if hasattr(form, field):
                    getattr(form, field).errors.append(error)
        else:
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.user_list'))
    
    return render_template('admin/users/edit.html', form=form, user=user)

@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id: int) -> Response:
    if current_user.id == user_id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.user_list'))
    
    if UserService.delete_user(user_id):
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found.', 'danger')
    
    return redirect(url_for('admin.user_list'))
