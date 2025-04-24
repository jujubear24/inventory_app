from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional, Length
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from app.models import Permission

def get_permissions():
    """Query function to fetch all permissions from the database."""
    return Permission.query.order_by(Permission.name).all()

class RoleEditForm(FlaskForm):
    """Form for editing a role's description and assigned permissions."""

    # Role name is usually not editable once created, so display it read-only
    name = StringField('Role Name', render_kw={'readonly': True})
    description = StringField('Description', validators=[Optional(), Length(max=255)])

    # Field to select multiple permissions
    permissions = QuerySelectMultipleField(
        'Assign Permissions',     
        query_factory=get_permissions, 
        get_label='name',        # Use the Permission.name attribute as the display label
        allow_blank=True,        # Allow a role to have no permissions selected
        validators=[Optional()]
    )
    submit = SubmitField('Update Role Permissions')


