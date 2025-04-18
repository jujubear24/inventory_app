from .db import db  
from .user import User 
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy.orm import relationship

# Define the OAuth model using the mixin provided by Flask-Dance
class OAuth(OAuthConsumerMixin, db.Model):
    """
    Stores OAuth credentials and links them to a User.
    Inherits provider, provider_user_id, created_at, and token columns
    from OAuthConsumerMixin.
    """
    __tablename__ = 'flask_dance_oauth' 
    
    # Foreign key to link this OAuth entry to a user in your database
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # Define the relationship back to the User model.
    # This allows you to easily access the User object from an OAuth object (oauth_entry.user)
    # and potentially access OAuth entries from a User object if you add a backref.
    user = relationship(User) # backref='oauth_connections' could be added to User if needed

    def __repr__(self):
        return f'<OAuth provider={self.provider} user_id={self.user_id}>'