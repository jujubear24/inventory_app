from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SubmitField
from decimal import ROUND_HALF_UP
from wtforms.validators import DataRequired, Length, NumberRange, Optional

# Form: Product
class ProductForm(FlaskForm):
    name = StringField(
        'Product Name',
        validators=[DataRequired(), Length(max=100)]
    )
    sku = StringField(
        'SKU',
        validators=[Optional(), Length(max=50)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional()]
    )
    price = DecimalField(
        'Price ($)',
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        rounding=ROUND_HALF_UP
    )
    stock_level = IntegerField(
        'Stock Level',
        validators=[DataRequired(), NumberRange(min=0)],
        default=0
    )
    low_stock_threshold = IntegerField(
        'Low Stock Threshold',
        validators=[DataRequired(), NumberRange(min=0)],
        default=10
    )
    submit = SubmitField('Save Product') # Label will be adjusted in route/template

# Form: Delete confirmation
class ConfirmDeleteForm(FlaskForm):
    """Simple form for confirming deletion."""
    submit = SubmitField('Confirm Delete')

