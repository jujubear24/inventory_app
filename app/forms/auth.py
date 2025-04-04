from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User
from typing import Optional

def optional_length(min=None, max=None):
    def _optional_length(form, field):
        if field.data and len(field.data) < min:
            raise ValidationError(f'Field must be at least {min} characters long if provided.')
        elif field.data and max and len(field.data) > max:
            raise ValidationError(f'Field cannot be longer than {max} characters.')
    return _optional_length

class LoginForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired()])
    password: PasswordField = PasswordField('Password', validators=[DataRequired()])
    remember_me: BooleanField = BooleanField('Remember Me')
    submit: SubmitField = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email: StringField = StringField('Email', validators=[DataRequired(), Email()])
    first_name: StringField = StringField('First Name', validators=[Length(max=64)])
    last_name: StringField = StringField('Last Name', validators=[Length(max=64)])
    password: PasswordField = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2: PasswordField = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit: SubmitField = SubmitField('Register')
    
    def validate_username(self, username: StringField) -> None:
        user: Optional[User] = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email: StringField) -> None:
        user: Optional[User] = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Length(max=64)])
    last_name = StringField('Last Name', validators=[Length(max=64)])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[optional_length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Save Changes')

