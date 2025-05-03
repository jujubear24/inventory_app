import pytest
from unittest.mock import patch
from app import create_app
from app.models.user import User
from app.models.db import (
    db as app_db,
)  # Alias to avoid conflict with db fixture if you add one
from config import config_by_name as config, TestingConfig
import logging
import os


# === FIXTURES ===
@pytest.fixture(scope="module")
def app():

    """Fixture to create and configure a new app instance for testing."""

    # Use 'testing' config and ensure necessary settings are present
    _app = create_app("testing")

    # Ensure essential test configurations are set
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "TEST_DATABASE_URI", "sqlite:///:memory:"
    )  # Use in-memory DB
    _app.config["WTF_CSRF_ENABLED"] = False  # Often disable CSRF for testing forms
    _app.config["LOGIN_DISABLED"] = (
        False  # Ensure login is enabled unless specifically testing disabled state
    )
    _app.config["SECRET_KEY"] = (
        "test-secret-key"  # Provide a dummy secret key for testing
    )

    yield _app


@pytest.fixture(scope="function", autouse=True)
def app_context(app):
    """Fixture to push an application context before each test."""
    with app.app_context():
        yield


# --- Test Configuration Loading and Checks ---


def test_create_app_uses_flask_env_when_no_config_name(monkeypatch):
    """
    Test create_app() uses FLASK_ENV to determine config
    when config_name is None. We'll set FLASK_ENV=testing.
    """
    monkeypatch.setenv('FLASK_ENV', 'testing')
    
    expected_config_class = config["testing"]

    assert expected_config_class == TestingConfig

    app = create_app()

    # Assert: Check values known to be set by TestingConfig
    assert 'TESTING' in app.config, "'TESTING' key not found in app.config"
    assert app.config['TESTING'] is True, "app.config['TESTING'] was not True, TestingConfig likely not loaded."

  
    assert 'SQLALCHEMY_DATABASE_URI' in app.config
    expected_uri = getattr(expected_config_class, 'SQLALCHEMY_DATABASE_URI', 'URI_NOT_IN_CLASS')
    assert app.config['SQLALCHEMY_DATABASE_URI'] == expected_uri
 
 
    assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI'], \
        "Expected in-memory SQLite DB URI for TestingConfig"


def test_create_app_testing_config():
    """Test creating app with 'testing' config name."""
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]  # Common testing setup


def test_create_app_missing_secret_key_raises_error(monkeypatch):
    """Test ValueError is raised if SECRET_KEY is missing."""

    # Temporarily remove SECRET_KEY from environment/config source
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setattr(config["testing"], "SECRET_KEY", None, raising=False)

    with pytest.raises(ValueError) as excinfo:
        create_app("testing")
    assert "SECRET_KEY is not configured" in str(excinfo.value)


@patch("app.__init__.get_app_config", return_value={})
def test_create_app_missing_db_uri_logs_warning_and_raises_error(
    mock_get_app_config, monkeypatch, caplog
):
    """Test warning logged and RuntimeError raised if SQLALCHEMY_DATABASE_URI is missing."""

    # 1. Get the config class object
    target_config_class = config["testing"]

    # 2. Set the URI to None on the class
    monkeypatch.setattr(target_config_class, "SQLALCHEMY_DATABASE_URI", None)

    # 3. Set log level to captire warnings
    caplog.set_level(logging.WARNING)

    # 4. Create the app AFTER patching the config class
    with pytest.raises(RuntimeError) as excinfo:
        # Call create_app within the raises block
        # The warning log should happen *before* the exception here
        app = create_app("testing")

    # 5. Check the exception message from Flask-SQLAlchemy
    assert "Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set" in str(
        excinfo.value
    )

    # 6. Check that the warning log WAS captured before the exception was raised

    log_messages = [rec.message for rec in caplog.records if rec.levelname == "WARNING"]
    assert any(
        "SQLALCHEMY_DATABASE_URI environment variable is not set" in msg
        for msg in log_messages
    ), "Expected warning log for missing SQLALCHEMY_DATABASE_URI not found."


@patch("app.__init__.get_app_config", return_value={})
def test_create_app_missing_google_keys_logs_warning(
    mock_get_app_config, monkeypatch, caplog
):
    """Test warnings logged if Google OAuth keys are missing."""

    target_config_class = config["testing"]
    monkeypatch.setattr(target_config_class, "GOOGLE_OAUTH_CLIENT_ID", None)
    monkeypatch.setattr(target_config_class, "GOOGLE_OAUTH_CLIENT_SECRET", None)

    # Ensure caplog captures WARNING level logs
    caplog.set_level(logging.WARNING)

    app = create_app("testing")

    log_messages = [rec.message for rec in caplog.records if rec.levelname == "WARNING"]

    print("Captured Logs:", caplog.text)

    assert any(
        "Google OAuth Client ID or Secret not configured" in msg for msg in log_messages
    )
    assert any(
        "Google OAuth secrets not set" in msg for msg in log_messages
    ), "Log message about secrets not set not found."


# --- Test Conditional Blueprint Registration ---


def test_create_app_registers_google_bp_if_keys_present(monkeypatch):
    """Test Google blueprint IS registered when keys are set."""
    # Ensure keys are present (they likely are in 'testing' by default)
    # Or explicitly set them if needed via monkeypatch:
    monkeypatch.setattr(config["testing"], "GOOGLE_OAUTH_CLIENT_ID", "dummy-id")
    monkeypatch.setattr(config["testing"], "GOOGLE_OAUTH_CLIENT_SECRET", "dummy-secret")

    app = create_app("testing")
    assert "google" in app.blueprints


def test_create_app_does_not_register_google_bp_if_keys_missing(monkeypatch):
    """Test Google blueprint is NOT registered when keys are missing."""
    monkeypatch.setattr(config["testing"], "GOOGLE_OAUTH_CLIENT_ID", None)
    monkeypatch.setattr(config["testing"], "GOOGLE_OAUTH_CLIENT_SECRET", None)

    app = create_app("testing")
    assert "google" not in app.blueprints


# --- Test Login Manager User Loader ---


def test_load_user_callback(app):
    """Test the user_loader callback for Flask-Login."""

    # We need a real app context and a user in the temp DB
    login_manager = app.login_manager
    user_loader_func = login_manager._user_callback

    with app.app_context():
        # Arrange: Create a user directly in the DB
        app_db.create_all()  # Create tables if using in-memory DB per test
        test_user = User(username="loader_test", email="loader@test.com")
        test_user.set_password("pw")
        app_db.session.add(test_user)
        app_db.session.commit()
        user_id = test_user.id

        # Act: Call the loader function directly
        loaded_user = user_loader_func(str(user_id))

        # Assert: Check if the correct user was loaded
        assert loaded_user is not None
        assert loaded_user.id == user_id
        assert loaded_user.username == "loader_test"

        # Test loading a non-existent user
        non_existent_user = user_loader_func("99999")
        assert non_existent_user is None


# --- Test Error Handlers ---


def test_404_error_handler(app):
    """Test the 404 error handler returns the correct template and status."""
    # Use the app's test client
    client = app.test_client()
    response = client.get("/a-route-that-does-not-exist-404")

    assert response.status_code == 404
    # Check for content unique to your 404.html template
    assert b"Page Not Found" in response.data  # Adjust text based on your template


# Add similar tests for 403 and 500 if desired.
# For 500, you might need to create a dummy route that raises an exception.
# E.g.,
# @test_app.route('/force500')
# def force_500():
#     raise Exception("Forced internal server error")
# client.get('/force500') -> check status 500, check template, mock db.session.rollback

# --- Test CLI Commands ---


@patch("app.db.create_all")  # Patch where create_all is called from
def test_init_db_command(mock_create_all, app):
    """Test the init-db CLI command."""

    runner = app.test_cli_runner()
    result = runner.invoke(args=["init-db"])

    assert result.exit_code == 0
    assert "Initialized the database." in result.output
    mock_create_all.assert_called_once()
