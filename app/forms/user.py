from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class UserForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email: StringField = StringField('Email', validators=[DataRequired(), Email()])
    first_name: StringField = StringField('First Name', validators=[Length(max=64)])
    last_name: StringField = StringField('Last Name', validators=[Length(max=64)])
    password: PasswordField = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2: PasswordField = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    is_admin: BooleanField = BooleanField('Admin User')
    submit: SubmitField = SubmitField('Create User')

class UserEditForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email: StringField = StringField('Email', validators=[DataRequired(), Email()])
    first_name: StringField = StringField('First Name', validators=[Length(max=64)])
    last_name: StringField = StringField('Last Name', validators=[Length(max=64)])
    password: PasswordField = PasswordField('Password', validators=[Optional(), Length(min=8)])
    password2: PasswordField = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_admin: BooleanField = BooleanField('Admin User')
    submit: SubmitField = SubmitField('Update User')

