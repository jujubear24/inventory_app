from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin # Assuming User already has this

class OAuth(OAuthConsumerMixin, db.Model):
    # Define foreign key relationship to your User model
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    # Define relationship back to the User model
    user = db.relationship(User)