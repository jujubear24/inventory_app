from .default import Config

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

    # Optional: set a fixed SECRET_KEY for predictable test sessions if needed
        # SECRET_KEY = 'testing-secret-key' # Use the one from base/env unless needed for tests
