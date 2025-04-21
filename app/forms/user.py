from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from app.models import Role

# Helper function to query roles for the form field
def get_roles():
    return Role.query.order_by(Role.name).all()




class UserForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email: StringField = StringField('Email', validators=[DataRequired(), Email()])
    first_name: StringField = StringField('First Name', validators=[Length(max=64)])
    last_name: StringField = StringField('Last Name', validators=[Length(max=64)])
    password: PasswordField = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2: PasswordField = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    roles = QuerySelectMultipleField(
        'Assign Roles',          
        query_factory=get_roles, # Function to load choices from DB
        get_label='name',       # Use the Role.name attribute as the display label for each choice
        allow_blank=True,       # Allow creating a user with no roles selected initially?
        validators=[Optional()] # Make selection optional for now
    )

    submit: SubmitField = SubmitField('Create User')

    

class UserEditForm(FlaskForm):
    username: StringField = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email: StringField = StringField('Email', validators=[DataRequired(), Email()])
    first_name: StringField = StringField('First Name', validators=[Length(max=64)])
    last_name: StringField = StringField('Last Name', validators=[Length(max=64)])
    password: PasswordField = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    password2: PasswordField = PasswordField('Confirm New Password', validators=[EqualTo('password')])

    roles = QuerySelectMultipleField(
        'Assign Roles',
        query_factory=get_roles,
        get_label='name',
        allow_blank=True,
        validators=[Optional()]
    )
    submit: SubmitField = SubmitField('Update User')

