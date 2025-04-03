from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User
from typing import Optional

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

