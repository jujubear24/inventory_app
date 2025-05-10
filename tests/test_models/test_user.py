import pytest
from unittest.mock import patch
from app.models.user import User

# Assuming your conftest.py provides 'app' and 'db' (or you manage db within app context)
# from app import db # If you need to directly interact with db session for creating test users


# You likely have a fixture to create a user already, if not, here's a simple one.
# If you have one in conftest.py that also adds to db, you might need to adjust
# how `new_user_model_only` is used if some tests don't want db persistence.
@pytest.fixture
def new_user_model_only(app):  # Renamed to indicate it's not added to DB by default
    """Fixture to create a new user instance (not saved to DB by this fixture)."""
    # App context is implicitly handled if 'app' fixture pushes one,
    # or ensure it's active if creating user within the test.
    with app.app_context():
        user = User(id=1, username="testuser", email="test@example.com")
        user.set_password("password123")  # Set a password hash
        return user


@pytest.fixture
def persisted_user(app):
    """Fixture to create and save a user to the database."""
    with app.app_context():
        from app import db  # Import db instance

        user = User(username="persisteduser", email="persist@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        yield user
        # Teardown: remove the user
        db.session.delete(user)
        db.session.commit()


def test_get_reset_password_token(
    app, new_user_model_only
):  # Uses app fixture for context
    """Test that a token is generated."""
    # The app fixture from your conftest should provide the app context
    token = new_user_model_only.get_reset_password_token()
    assert token is not None
    assert isinstance(token, str)


def test_verify_reset_password_token_valid(
    app, persisted_user
):  # Test with a user that can be queried
    """Test token verification with a valid token."""    

    token = persisted_user.get_reset_password_token()
    assert token is not None

    # User.query.get will be used by verify_reset_password_token
    verified_user = User.verify_reset_password_token(token)

    assert verified_user is not None
    assert verified_user.id == persisted_user.id
    assert verified_user.email == persisted_user.email


def test_verify_reset_password_token_expired(app, new_user_model_only):
    """Test token verification with an expired token."""
    # App context from 'app' fixture
    token = new_user_model_only.get_reset_password_token()
    assert token is not None

    # Simulate time passing so token is older than max_age_sec=0
    # A slight delay, though direct time mocking via patch is more precise for strict expiry.
    # For max_age=0, any token is essentially expired.
    # time.sleep(0.01) # May not be necessary if max_age_sec is 0

    verified_user = User.verify_reset_password_token(token, max_age_sec=0)
    assert verified_user is None


def test_verify_reset_password_token_invalid_signature(app, new_user_model_only):
    """Test token verification with an invalid/tampered token."""
    # App context from 'app' fixture
    token = new_user_model_only.get_reset_password_token()
    invalid_token = token + "tampered"
    verified_user = User.verify_reset_password_token(invalid_token)
    assert verified_user is None

    completely_invalid_token = "this.is.not.a.valid.token"
    verified_user_invalid_format = User.verify_reset_password_token(
        completely_invalid_token
    )
    assert verified_user_invalid_format is None


def test_verify_reset_password_token_user_not_found_after_token_creation(
    app, new_user_model_only
):
    """Test token for a user_id that no longer exists (user deleted after token issued)."""
    # App context from 'app' fixture
    # This user (ID 1 from new_user_model_only) is not in the DB unless persisted.
    # Let's assume verify_reset_password_token will try User.query.get(1)

    token = new_user_model_only.get_reset_password_token()  # User ID is 1 from fixture
    assert token is not None

    # Mock User.query.get to simulate user not found in the DB for this specific call
    with patch("app.models.user.User.query") as mock_query:
        mock_query.get.return_value = None  # Simulate User.query.get(1) returns None
        verified_user = User.verify_reset_password_token(token)
        assert verified_user is None
        mock_query.get.assert_called_once_with(new_user_model_only.id)


def test_token_methods_no_secret_key(app, new_user_model_only, caplog):
    """Test token methods when SECRET_KEY is not configured."""
    # App context from 'app' fixture
    original_secret_key = app.config.get("SECRET_KEY")
    try:
        app.config["SECRET_KEY"] = None  # Temporarily remove secret key

        # Test get_reset_password_token
        token = new_user_model_only.get_reset_password_token()
        assert token is None
        assert (
            "SECRET_KEY not set. Cannot generate password reset token." in caplog.text
        )
        caplog.clear()  # Clear logs for the next assertion

        # Test verify_reset_password_token (needs a dummy token string)
        verified_user = User.verify_reset_password_token("dummytoken")
        assert verified_user is None
        assert "SECRET_KEY not set. Cannot verify password reset token." in caplog.text
    finally:
        app.config["SECRET_KEY"] = original_secret_key  # Restore secret key
