"""Test configuration for the inventory app."""

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_TRACK_MODIFICATIONS = False
TESTING = True
# Disable CSRF protection in testing
WTF_CSRF_ENABLED = False

