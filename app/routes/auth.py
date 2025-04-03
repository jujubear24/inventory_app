from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.db import db
from app.forms.auth import LoginForm, RegistrationForm
from typing import Union, Optional

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, redirect]:
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page: Optional[str] = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout() -> redirect:
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, redirect]:
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form: RegistrationForm = RegistrationForm()
    if form.validate_on_submit():
        user: User = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

