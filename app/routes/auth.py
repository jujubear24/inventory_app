from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.db import db
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm, RequestResetForm, ResetPasswordForm
from datetime import datetime
from typing import Union
from flask_mail import Message
from app import mail


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# --- Email Sending Helper Function ---

def send_password_reset_email(user: User) -> None:
    """Generates a password reset token and sends it to the user."""
    token = user.get_reset_password_token()
    if not token:
        flash(
            "Failed to generate a reset token. Please try again or contact support.",
            "danger",
        )
        current_app.logger.error(f"Token generation failed for user {user.email}")
        return

    # Ensure MAIL_DEFAULT_SENDER is configured
    sender_email = current_app.config.get("MAIL_DEFAULT_SENDER")
    if not sender_email:
        current_app.logger.error(
            "MAIL_DEFAULT_SENDER is not configured. Cannot send password reset email."
        )
        flash(
            "The application is not configured to send emails. Please contact support.",
            "danger",
        )
        return

    msg = Message(
        "Password Reset Request", sender=sender_email, recipients=[user.email]
    )
    reset_url = url_for("auth.reset_token", token=token, _external=True)
    msg.body = f"""To reset your password, visit the following link:
            {reset_url}
        If you did not make this request then simply ignore this email and no changes will be made.
        This token is valid for 30 minutes.
        """
    # For development with MAIL_BACKEND = 'console', this will print to console.
    # In production, it will send an actual email.

    # --- DEVELOPMENT LOGGING ---
    if current_app.config.get("MAIL_SUPPRESS_SEND", False) or current_app.debug:
        current_app.logger.info("---- PASSWORD RESET EMAIL (SIMULATED) ----")
        current_app.logger.info(f"To: {user.email}")
        current_app.logger.info(f"From: {sender_email}")
        current_app.logger.info(f"Subject: {msg.subject}")
        current_app.logger.info(f"Body:\n{msg.body}")
        current_app.logger.info("---- END OF SIMULATED EMAIL ----")
    # --- END DEVELOPMENT LOGGING ---

    try:
        mail.send(msg)
        if not current_app.config.get("MAIL_SUPPRESS_SEND"):
            current_app.logger.info(
                f"Password reset email actually attempted for {user.email}"
            )
       
    except Exception as e:
        current_app.logger.error(
            f"Failed to send password reset email to {user.email}: {e}", exc_info=True
        )
        flash(
            "There was an error sending the password reset email. Please try again later or contact support.",
            "danger",
        )


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.product_list'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.password_hash and  user.check_password(form.password.data):
            # Login the user
            login_user(user, remember=form.remember_me.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to the dashboard
            return redirect(url_for('main.product_list'))
        
        # Invalid login attempt
        flash('Invalid username or password, or login method.', 'danger')
    
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
        username_changed = form.username.data != current_user.username
        email_changed = form.email.data != current_user.email

        if username_changed and User.query.filter(User.username == form.username.data, User.id != current_user.id).first():
            form.username.errors.append('Username already taken.')
        if email_changed and User.query.filter(User.email == form.email.data, User.id != current_user.id).first():
            form.email.errors.append('Email already registered by another user.')

        if form.username.errors or form.email.errors:
            return render_template('auth/profile.html', form=form, title="My Profile")

        # Password change logic
        if form.new_password.data:
            if not current_user.password_hash: # User is likely OAuth only
                form.current_password.errors.append("Cannot change password for accounts created via external providers without setting an initial password.")
            elif not form.current_password.data:
                form.current_password.errors.append('Current password is required to set a new password.')
            elif not current_user.check_password(form.current_password.data):
                form.current_password.errors.append('Incorrect current password.')

            if form.current_password.errors: # Check if any password related errors occurred
                return render_template('auth/profile.html', form=form, title="My Profile")

            current_user.set_password(form.new_password.data)
            flash('Your password has been updated.', 'success')

        # Update other user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        try:
            db.session.commit()
            flash("Your profile has been updated successfully!", "success")
            return redirect(
                url_for("auth.profile")
            )  # Redirect to refresh or show updated info
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error updating profile for {current_user.username}: {e}",
                exc_info=True,
            )
            flash(
                "An error occurred while updating your profile. Please try again.",
                "danger",
            )

    return render_template('auth/profile.html', form=form)


#  -- Password Reset Routes ---

@auth_bp.route("/reset_password", methods=["GET", "POST"])
def request_reset_token():
    if current_user.is_authenticated:
        return redirect(url_for("main.product_list"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # The form validator already checks if user exists and has password_hash
        if user:
            send_password_reset_email(user)
            flash(
                "An email has been sent with instructions to reset your password.",
                "info",
            )
            return redirect(url_for("auth.login"))
        # else: # Should be caught by form.validate_email
        # flash('Email address not found or user registered via OAuth.', 'warning')

    return render_template(
        "auth/request_reset_token.html", title="Request Password Reset", form=form
    )


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.product_list"))

    user = User.verify_reset_password_token(token)
    if user is None:
        flash("That is an invalid or expired token.", "warning")
        return redirect(url_for("auth.request_reset_token"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been updated! You are now able to log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_token.html", title="Reset Password", form=form, token=token
    )
