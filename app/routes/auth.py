from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
)
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.db import db
from app.forms.auth import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    RequestResetForm,
    ResetPasswordForm,
)
from datetime import datetime
from typing import Union
from flask_mail import Message
from app import mail


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


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

    if current_app.config.get("MAIL_SUPPRESS_SEND", False) or current_app.debug:
        current_app.logger.info("---- PASSWORD RESET EMAIL (SIMULATED) ----")
        current_app.logger.info(f"To: {user.email}")
        current_app.logger.info(f"From: {sender_email}")
        current_app.logger.info(f"Subject: {msg.subject}")
        current_app.logger.info(f"Body:\n{msg.body}")
        current_app.logger.info("---- END OF SIMULATED EMAIL ----")

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


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.product_list"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.password_hash and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for("main.product_list"))

        flash("Invalid username or password, or login method.", "danger")

    return render_template("auth/login.html", form=form, title="Login")


@auth_bp.route("/logout")
@login_required
def logout() -> redirect:
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> Union[str, redirect]:
    if current_user.is_authenticated:
        return redirect(url_for("main.product_list"))

    form: RegistrationForm = RegistrationForm()
    if form.validate_on_submit():
        user: User = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Register")


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    print(f"\n[PROFILE ROUTE ENTRY] Request method: {request.method}")
    form = ProfileForm(obj=current_user)
    if request.method == "POST":
        print(f"[PROFILE ROUTE POST] Initial form data from request: {request.form}")
        print(
            f"[PROFILE ROUTE POST] Form object before validation: username='{form.username.data}', email='{form.email.data}'"
        )

    if form.validate_on_submit():
        print("[PROFILE ROUTE] form.validate_on_submit() is TRUE.")
        print(
            f"[PROFILE ROUTE] Form data after successful basic validation: username='{form.username.data}', email='{form.email.data}', first_name='{form.first_name.data}', last_name='{form.last_name.data}'"
        )
        print(
            f"[PROFILE ROUTE] current_user state: id={current_user.id}, username='{current_user.username}', email='{current_user.email}'"
        )

        username_changed = form.username.data != current_user.username
        email_changed = form.email.data != current_user.email

        print(
            f"[PROFILE ROUTE] username_changed: {username_changed}, email_changed: {email_changed}"
        )

        if username_changed:
            if User.query.filter(
                User.username == form.username.data, User.id != current_user.id
            ).first():
                form.username.errors.append("Username already taken.")
                print(
                    f"[PROFILE ROUTE] Added username error for '{form.username.data}'. Form errors: {form.errors}"
                )

        if email_changed:
            if User.query.filter(
                User.email == form.email.data, User.id != current_user.id
            ).first():
                form.email.errors.append("Email already registered by another user.")
                print(
                    f"[PROFILE ROUTE] Added email error for '{form.email.data}'. Form errors: {form.errors}"
                )

        if form.username.errors or form.email.errors:
            print(
                f"[PROFILE ROUTE] Re-rendering due to username/email uniqueness errors. Final form errors: {form.errors}"
            )
            flash("Profile update failed. Please correct the errors below.", "danger")
            return render_template("auth/profile.html", form=form, title="My Profile")

        # Password change logic
        password_related_error = False  # Initialize the flag
        if form.new_password.data:
            print("[PROFILE ROUTE] Attempting password change. new_password provided.")
            # **FIX**: Initialize password_related_error to False here
            password_related_error = False

            if not current_user.password_hash:
                form.current_password.errors.append(
                    "Cannot change password for accounts created via external providers without setting an initial password."
                )
                password_related_error = True
            elif not form.current_password.data:
                form.current_password.errors.append(
                    "Current password is required to set a new password."
                )
                password_related_error = True
            elif not current_user.check_password(form.current_password.data):
                form.current_password.errors.append("Incorrect current password.")
                password_related_error = True

            if form.new_password.errors or form.confirm_new_password.errors:
                password_related_error = True

            if password_related_error:
                print(
                    f"[PROFILE ROUTE] Re-rendering due to password related errors. Final form errors: {form.errors}"
                )
                flash(
                    "Password change failed. Please correct the errors below.", "danger"
                )
                return render_template(
                    "auth/profile.html", form=form, title="My Profile"
                )

            current_user.set_password(form.new_password.data)
            # Flash for password update moved to after successful commit

        # Update other user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        try:
            db.session.commit()
            print("[PROFILE ROUTE] db.session.commit() successful. Redirecting.")

            if form.new_password.data and not password_related_error:
                flash(
                    "Your profile and password have been updated successfully!",
                    "success",
                )
            else:
                flash("Your profile has been updated successfully!", "success")
            return redirect(url_for("auth.profile"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error updating profile for {current_user.username}: {e}",
                exc_info=True,
            )
            print(
                f"[PROFILE ROUTE] Exception during db.session.commit(): {e}. Re-rendering. Final form errors: {form.errors}"
            )
            flash(
                "An error occurred while updating your profile. Please try again.",
                "danger",
            )
            return render_template("auth/profile.html", form=form, title="My Profile")
    else:
        if request.method == "POST":
            print(
                f"[PROFILE ROUTE] form.validate_on_submit() is FALSE. Form errors from WTForms validation: {form.errors}"
            )

    return render_template("auth/profile.html", form=form, title="My Profile")


#  -- Password Reset Routes ---
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def request_reset_token():
    if current_user.is_authenticated:
        return redirect(url_for("main.product_list"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash(
                "An email has been sent with instructions to reset your password.",
                "info",
            )
            return redirect(url_for("auth.login"))
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
