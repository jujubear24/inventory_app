from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.db import db
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm
from datetime import datetime
from typing import Union

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.product_list'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            # Login the user
            login_user(user, remember=form.remember_me.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to the dashboard
            return redirect(url_for('main.product_list'))
        
        # Invalid login attempt
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout() -> redirect:
    logout_user()
    return redirect(url_for('main.product_list'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, redirect]:
    if current_user.is_authenticated:
        return redirect(url_for('main.product_list'))
    
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


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Check if username or email is being changed
        if form.username.data != current_user.username and User.query.filter_by(username=form.username.data).first():
            form.username.errors.append('Username already taken')
            return render_template('auth/profile.html', form=form)
        
        if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first():
            form.email.errors.append('Email already registered')
            return render_template('auth/profile.html', form=form)
        
        # Check current password if attempting to change password
        if form.new_password.data:
            if not form.current_password.data:
                form.current_password.errors.append('Current password is required to set a new password')
                return render_template('auth/profile.html', form=form)
            
            if not current_user.check_password(form.current_password.data):
                form.current_password.errors.append('Incorrect password')
                return render_template('auth/profile.html', form=form)
            
            current_user.set_password(form.new_password.data)
        
        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form)