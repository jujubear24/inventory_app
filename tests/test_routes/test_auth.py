import pytest
from flask import url_for
from app import create_app
from app.models.db import db
from app.models.user import User
from unittest.mock import patch, MagicMock


# --- Fixtures ---
@pytest.fixture(scope="module")
def test_app():
    """Fixture to set up the Flask app for testing."""
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SERVER_NAME"] = "localhost"
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key"  # Needed for session/flash messages

    with app.app_context():
        db.create_all()
        # Create a test user (optional, but useful for login/profile tests)
        test_user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        test_user.set_password("password")
        db.session.add(test_user)
        db.session.commit()

        yield app
        # Cleanup (handled by in-memory DB)


@pytest.fixture(scope="function")
def test_client(test_app):
    """Fixture for the Flask test client."""
    with test_app.test_client() as client:
        with test_app.app_context():  # Ensure context for db operations within tests
            yield client


@pytest.fixture(scope="function")
def logged_in_client(test_client):
    """Fixture for a client already logged in as the test user."""
    # Login the user 'testuser'
    test_client.post(
        url_for("auth.login"),
        data={"username": "testuser", "password": "password"},
        follow_redirects=True,
    )
    yield test_client
    # Logout after test
    test_client.get(url_for("auth.logout"), follow_redirects=True)


# --- Test Class for Auth Routes ---

class TestAuthRoutes:

    # Use function scope fixture to ensure app context for each test method
    @pytest.fixture(autouse=True)
    def setup_app_context(self, test_app):
        with test_app.app_context():
            yield

    # === Login Route Tests (/auth/login) ===

    #  Test login page 'GET' request
    def test_login_page_get(self, test_client):
        """Test GET request to the login page."""
        response = test_client.get(url_for("auth.login"))
        assert response.status_code == 200
        assert b"Login" in response.data  # Check for a keyword in the template

    @patch("app.routes.auth.User.query")  # Mock the database query
    @patch("app.routes.auth.db.session.commit")  # Mock db commit
    @patch("app.routes.auth.login_user")  # Mock flask_login function

    # Test login post success 
    def test_login_post_success(
        self, mock_login_user, mock_commit, mock_user_query, test_client
    ):
        """Test successful POST request to login."""
        # Mock the user found by the query
        mock_user = MagicMock(spec=User)
        mock_user.check_password.return_value = True
        mock_user.last_login = None  # To check it gets updated
        mock_user_query.filter_by.return_value.first.return_value = mock_user

        response = test_client.post(
            url_for("auth.login"),
            data={"username": "testuser", "password": "password"},
            follow_redirects=False,
        )  # Important: check redirect before following

        assert response.status_code == 302  # Expect redirect on success
        assert response.location == url_for(
            "main.product_list", _external=False
        )  # Check redirect URL
        mock_user_query.filter_by.assert_called_once_with(username="testuser")
        mock_user.check_password.assert_called_once_with("password")
        mock_login_user.assert_called_once_with(mock_user, remember=False)
        assert mock_user.last_login is not None  # Check last_login was updated
        mock_commit.assert_called_once()

    def test_login_post_invalid_credentials(self, test_client):
        """Test POST request with invalid credentials."""
        response = test_client.post(
            url_for("auth.login"),
            data={"username": "wronguser", "password": "wrongpassword"},
            follow_redirects=True,
        )  # Follow redirects to check flash message

        assert response.status_code == 200  # Should stay on login page
        assert b"Invalid username or password" in response.data  # Check flash message

    def test_login_already_authenticated(self, logged_in_client):
        """Test accessing login page when already logged in."""
        response = logged_in_client.get(url_for("auth.login"), follow_redirects=False)
        assert response.status_code == 302
        assert response.location == url_for("main.product_list", _external=False)

    # === Logout Route Tests (/auth/logout) ===

    def test_logout_success(self, logged_in_client):
        """Test successful logout."""
        response = logged_in_client.get(url_for("auth.logout"), follow_redirects=False)
        assert response.status_code == 302
        assert response.location == url_for("main.product_list", _external=False)

        # Verify user is logged out by trying to access a protected route (like profile)
        profile_response = logged_in_client.get(
            url_for("auth.profile"), follow_redirects=False
        )
        assert profile_response.status_code == 302  # Should redirect to login
        assert profile_response.location.startswith(
            url_for("auth.login", _external=False)
        )

    def test_logout_not_logged_in(self, test_client):
        """Test accessing logout when not logged in (should redirect to login)."""
        response = test_client.get(url_for("auth.logout"), follow_redirects=False)
        assert response.status_code == 302
        assert response.location.startswith(
            url_for("auth.login", _external=False)
        )  # @login_required redirects

    # === Register Route Tests (/auth/register) ===

    def test_register_page_get(self, test_client):
        """Test GET request to the registration page."""
        response = test_client.get(url_for("auth.register"))
        assert response.status_code == 200
        assert b"Register" in response.data

    @patch("app.routes.auth.db.session.add")
    @patch("app.routes.auth.db.session.commit")
    def test_register_post_success(self, mock_commit, mock_add, test_client):
        """Test successful POST request to register."""
        response = test_client.post(
            url_for("auth.register"),
            data={
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "newpassword",
                "password2": "newpassword",  # Assuming you have confirm password field
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.location == url_for("auth.login", _external=False)
        mock_add.assert_called_once()  # Check user object was added
        mock_commit.assert_called_once()

        # Check flash message after redirect
        redirect_response = test_client.get(response.location)
        assert b"Registration successful! Please log in." in redirect_response.data

    def test_register_post_validation_error(self, test_client):
        """Test POST request with validation errors (e.g., mismatched passwords)."""
        response = test_client.post(
            url_for("auth.register"),
            data={
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "newpassword",
                "password2": "wrongpassword",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200  # Should stay on register page
        assert (
            b"Field must be equal to password." in response.data
        )  # Check WTForms error message

    def test_register_already_authenticated(self, logged_in_client):
        """Test accessing register page when already logged in."""
        response = logged_in_client.get(
            url_for("auth.register"), follow_redirects=False
        )
        assert response.status_code == 302
        assert response.location == url_for("main.product_list", _external=False)

    # === Profile Route Tests (/auth/profile) ===

    def test_profile_page_get_unauthenticated(self, test_client):
        """Test GET request to profile page when not logged in."""
        response = test_client.get(url_for("auth.profile"), follow_redirects=False)
        assert response.status_code == 302
        assert response.location.startswith(url_for("auth.login", _external=False))

    def test_profile_page_get_authenticated(self, logged_in_client):
        """Test GET request to profile page when logged in."""
        response = logged_in_client.get(url_for("auth.profile"))
        assert response.status_code == 200
        assert b"My Profile" in response.data  # Check for title or specific content
        assert b"testuser" in response.data  # Check if current user's data is shown

    @patch("app.routes.auth.db.session.commit")
    def test_profile_post_update_success_no_password(
        self, mock_commit, logged_in_client, test_app
    ):
        """Test successful POST to update profile (no password change)."""

        with test_app.app_context():
            user_before = User.query.filter_by(username="testuser").first()
            # Add assertion to ensure user exists
            assert user_before is not None, "Test user 'testuser' not found in fixture."
            # Verify initial state (should work now)
            assert user_before.first_name == "Test"

        with patch("app.routes.auth.User.query") as mock_user_query_cm:

            # Configure the context manager's mock for conflict checks
            mock_user_query_cm.filter_by.return_value.first.return_value = None

            # Make the POST request
            response = logged_in_client.post(
                url_for("auth.profile"),
                data={
                    "username": "testuser",
                    "email": "test_updated@example.com",  # Update email
                    "first_name": "TestUpdated",  # Update first name
                    "last_name": "UserUpdated",  # Update last name
                    "current_password": "",  # No password change
                    "new_password": "",
                    "confirm_new_password": "",
                },
                follow_redirects=False,
            )  # Check redirect before following it

        # --- Assertions (Mock is inactive) ---
        assert response.status_code == 302  # Expect redirect
        assert response.location == url_for("auth.profile", _external=False)
        mock_commit.assert_called_once()  # Check DB commit was called

        redirect_response = logged_in_client.get(response.location)
        assert b"Your profile has been updated successfully!" in redirect_response.data

        # --- Verify changes in DB (Optional but good - Mock is inactive) ---
        with test_app.app_context():
            user_after = User.query.filter_by(username="testuser").first()
            assert user_after is not None
            assert user_after.email == "test_updated@example.com"
            assert user_after.first_name == "TestUpdated"
            assert user_after.last_name == "UserUpdated"


    # Test profile update success with password
    @patch("app.routes.auth.db.session.commit")
    def test_profile_post_update_success_with_password(
        self, mock_commit, logged_in_client, test_app
    ):
        """Test successful POST to update profile including password."""

        # --- Step 1: Get the actual user from DB first ---
        with test_app.app_context():
            user_before = User.query.filter_by(username="testuser").first()
            # Add an assertion to ensure the user exists from the fixture setup
            assert (
                user_before is not None
            ), "Test user 'testuser' could not be found in the database fixture."
            old_password_hash = user_before.password_hash

        # --- Step 2: NOW configure the mock for the route handler's checks ---
        with patch("app.routes.auth.User.query") as mock_user_query_cm:
            mock_user_query_cm.filter_by.return_value.first.return_value = None

            # --- Step 3: Make the POST request ---
            response = logged_in_client.post(
                url_for("auth.profile"),
                data={
                    "username": "testuser",  # Or a new username if you want to test that change too
                    "email": "test.pw.updated@example.com",  # Example: change email
                    "first_name": "Test",
                    "last_name": "User",
                    "current_password": "password",
                    "new_password": "newpassword",
                    "confirm_new_password": "newpassword",
                },
                follow_redirects=True,
            )  # Follow redirect to check flash

        # --- Step 4: Assertions ---
        assert response.status_code == 200  # Should be back on profile page
        assert b"Your profile has been updated successfully!" in response.data
        mock_commit.assert_called_once()  # Check that the commit was called in the route

        # --- Step 5: Verify changes in DB (Optional but good) ---
        with test_app.app_context():
            user_after = User.query.filter_by(
                username="testuser"
            ).first()  # Fetch updated user
            assert user_after is not None
            assert user_after.password_hash != old_password_hash
            assert user_after.check_password(
                "newpassword"
            )  # Check if new password works
            assert (
                user_after.email == "test.pw.updated@example.com"
            )  # Verify other fields updated

    def test_profile_post_incorrect_current_password(self, logged_in_client):
        """Test POST to update profile with incorrect current password."""
        response = logged_in_client.post(
            url_for("auth.profile"),
            data={
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "current_password": "wrongpassword",  # Incorrect
                "new_password": "newpassword",
                "confirm_new_password": "newpassword",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200  # Stay on profile page
        assert b"Incorrect password" in response.data  # Check error message

    @patch("app.routes.auth.User.query")
    def test_profile_post_username_taken(
        self, mock_user_query, logged_in_client, test_app
    ):
        """Test POST to update profile with a username that's already taken."""
        # Mock the query to find an existing user with the new username
        existing_user_mock = MagicMock(spec=User)
        mock_user_query.filter_by.return_value.first.return_value = existing_user_mock

        response = logged_in_client.post(
            url_for("auth.profile"),
            data={
                "username": "takenuser",  # Attempting to change to this
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                # ... other fields ...
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Username already taken" in response.data
        # Make sure the specific filter was called for the username
        mock_user_query.filter_by.assert_any_call(username="takenuser")
