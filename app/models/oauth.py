from datetime import datetime, timezone
from .db import db  
from .user import User 
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, JSON

# Define the OAuth model
class OAuth(OAuthConsumerMixin, db.Model):
    """
    Stores OAuth credentials and links them to a User.
    Inherits provider, provider_user_id, created_at, and token columns
    from OAuthConsumerMixin.
    """
    __tablename__ = 'flask_dance_oauth' 
    
    id = db.Column(db.Integer, primary_key=True) 
    
    # Foreign key to link this OAuth entry to a user in your database
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)

    # Define the relationship back to the User model.
    user = relationship(User) # backref='oauth_connections' could be added to User if needed

    provider = Column(String(50), nullable=False)  # OAuth provider name (e.g., 'google', 'facebook')
    provider_user_id = Column(String(256), nullable=True)
    token = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    # created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(datetime.timezone.utc))
    

    def __repr__(self):
        return f'<OAuth provider={self.provider} user_id={self.user_id}>'