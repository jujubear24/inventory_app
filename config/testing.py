from .default import Config
import os 

class TestingConfig(Config):
    TESTING = True
    DEBUG = True 

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

    # Optional: set a fixed SECRET_KEY for predictable test sessions if needed
        # SECRET_KEY = 'testing-secret-key' # Use the one from base/env unless needed for tests
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', 'dummy_test_id')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', 'dummy_test_secret')
