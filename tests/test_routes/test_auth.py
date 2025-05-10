import pytest
from flask import url_for
from unittest.mock import patch, MagicMock
from app.models.user import User
from app.models.db import db as _db  # Alias to avoid conflict

# Fixtures 'app' and 'client' are expected to be sourced from tests/conftest.py


@pytest.fixture(scope="function")
def test_user(app):  # Depends on 'app' from conftest.py
    """Creates and yields a standard test user in the database for a single test."""
    with app.app_context():
        # Ensure a clean state for 'testuser' for each test function
        user = User.query.filter_by(username="testuser").first()
        if user:
            _db.session.delete(user)
            _db.session.commit()

        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        user.set_password("password")
        _db.session.add(user)
        _db.session.commit()
        yield user


@pytest.fixture(scope="function")
def logged_in_client(
    client, test_user, app
):  # Depends on 'client' from conftest.py and local 'test_user'
    """Fixture for a client already logged in as the 'testuser'."""
    with app.app_context():  # Ensures url_for works if called outside a request context
        login_url = url_for("auth.login")

    client.post(
        login_url,
        data={"username": test_user.username, "password": "password"},
        follow_redirects=True,
    )
    yield client


# --- Test Class for Auth Routes ---
class TestAuthRoutes:
    """Test suite for authentication routes."""

    # === Login Route Tests (/auth/login) ===
    def test_login_page_get(self, client):  # Uses 'client' from conftest.py
        response = client.get(url_for("auth.login"))
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_login_success(
        self, client, test_user, app
    ):  # Uses 'client', 'test_user', 'app'
        with app.app_context():
            loaded_test_user = User.query.filter_by(username=test_user.username).first()
            assert loaded_test_user is not None
            assert loaded_test_user.first_name == "Test"

        response = client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": "password",
                "remember_me": False,
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.location == url_for("main.product_list", _external=False)

        response_redirected = client.get(response.location)
        assert b"Welcome, Test" in response_redirected.data

    def test_login_post_invalid_credentials(self, client, test_user):
        response = client.post(
            url_for("auth.login"),
            data={"username": test_user.username, "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_user_not_exist(self, client):
        response = client.post(
            url_for("auth.login"),
            data={"username": "nonexistentuser", "password": "password"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_login_already_authenticated(self, logged_in_client):
        response = logged_in_client.get(url_for("auth.login"), follow_redirects=False)
        assert response.status_code == 302
        assert response.location == url_for("main.product_list", _external=False)

    # === Logout Route Tests (/auth/logout) ===
    def test_logout_success(
        self, logged_in_client, app
    ):  # Added app for context if url_for needs it outside req
        with (
            app.app_context()
        ):  # Ensure context for url_for if called outside of a client request
            logout_url = url_for("auth.logout")
            login_url = url_for("auth.login")
            profile_url = url_for("auth.profile")

        response = logged_in_client.get(logout_url, follow_redirects=False)
        assert response.status_code == 302
        assert response.location == login_url

        response_redirected = logged_in_client.get(
            response.location, follow_redirects=True
        )
        assert b"You have been logged out." in response_redirected.data

        profile_response = logged_in_client.get(profile_url, follow_redirects=False)
        assert profile_response.status_code == 302
        assert profile_response.location.startswith(login_url)

    def test_logout_not_logged_in(self, client, app):
        with app.app_context():
            logout_url = url_for("auth.logout")
            login_url_start = url_for("auth.login")
        response = client.get(logout_url, follow_redirects=False)
        assert response.status_code == 302
        assert response.location.startswith(login_url_start)

    # === Register Route Tests (/auth/register) ===
    def test_register_page_get(self, client):
        response = client.get(url_for("auth.register"))
        assert response.status_code == 200
        assert b"Register" in response.data

    @patch("app.routes.auth.db.session.add")
    @patch("app.routes.auth.db.session.commit")
    def test_register_post_success(self, mock_commit, mock_add, client, app):
        with app.app_context():
            login_url = url_for("auth.login")
            register_url = url_for("auth.register")
        response = client.post(
            register_url,
            data={
                "username": "newuser",
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "newpassword",
                "password2": "newpassword",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.location == login_url
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

        redirect_response = client.get(response.location, follow_redirects=True)
        assert b"Registration successful! Please log in." in redirect_response.data

    def test_register_post_validation_error(self, client):
        response = client.post(
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
        assert response.status_code == 200
        assert b"Field must be equal to password." in response.data

    def test_register_already_authenticated(self, logged_in_client, app):
        with app.app_context():
            register_url = url_for("auth.register")
            dashboard_url = url_for("main.product_list")
        response = logged_in_client.get(register_url, follow_redirects=False)
        assert response.status_code == 302
        assert response.location == dashboard_url

    # === Profile Route Tests (/auth/profile) ===
    def test_profile_page_get_unauthenticated(self, client, app):
        with app.app_context():
            profile_url = url_for("auth.profile")
            login_url_start = url_for("auth.login")
        response = client.get(profile_url, follow_redirects=False)
        assert response.status_code == 302
        assert response.location.startswith(login_url_start)

    def test_profile_page_get_authenticated(self, logged_in_client, app, test_user):
        with app.app_context():
            response = logged_in_client.get(url_for("auth.profile"))
            assert response.status_code == 200
            assert b"My Profile" in response.data
            assert test_user.username.encode() in response.data

    @patch("app.routes.auth.db.session.commit")
    def test_profile_post_update_success_no_password(
        self, mock_commit, logged_in_client, app, test_user
    ):
        with app.app_context():
            original_first_name = test_user.first_name
            assert original_first_name == "Test"

            profile_url = url_for("auth.profile")

        with patch("app.routes.auth.User.query") as mock_user_query_in_route:
            mock_user_query_in_route.filter.return_value.first.return_value = None

            response = logged_in_client.post(
                profile_url,
                data={
                    "username": test_user.username,
                    "email": "test_updated@example.com",
                    "first_name": "TestUpdated",
                    "last_name": "UserUpdated",
                    "current_password": "",
                    "new_password": "",
                    "confirm_new_password": "",
                },
                follow_redirects=False,
            )

        assert (
            response.status_code == 302
        ), f"Expected 302, got {response.status_code}. Data: {response.data.decode()}"
        assert response.location == profile_url
        mock_commit.assert_called_once()

        response_redirected = logged_in_client.get(response.location)
        assert (
            b"Your profile has been updated successfully!" in response_redirected.data
        )

        with app.app_context():
            user_after = User.query.filter_by(username=test_user.username).first()
            assert user_after.email == "test_updated@example.com"
            assert user_after.first_name == "TestUpdated"

    @patch("app.routes.auth.db.session.commit")
    def test_profile_post_update_success_with_password(
        self, mock_commit, logged_in_client, app, test_user
    ):
        with app.app_context():
            user_before = User.query.filter_by(username=test_user.username).first()
            assert user_before is not None
            old_password_hash = user_before.password_hash
            profile_url = url_for("auth.profile")

        with patch("app.routes.auth.User.query") as mock_user_query_in_route:
            mock_user_query_in_route.filter.return_value.first.return_value = None

            response = logged_in_client.post(
                profile_url,
                data={
                    "username": test_user.username,
                    "email": "test.pw.updated@example.com",
                    "first_name": "TestPW",
                    "last_name": "UserPW",
                    "current_password": "password",
                    "new_password": "newpassword",
                    "confirm_new_password": "newpassword",
                },
                follow_redirects=False,
            )

        assert (
            response.status_code == 302
        ), f"Expected 302, got {response.status_code}. Data: {response.data.decode()}"
        assert response.location == profile_url
        mock_commit.assert_called_once()

        response_redirected = logged_in_client.get(response.location)
        assert (
            b"Your profile and password have been updated successfully!"
            in response_redirected.data
        )

        with app.app_context():
            user_after = User.query.filter_by(username=test_user.username).first()
            assert user_after.email == "test.pw.updated@example.com"
            assert user_after.first_name == "TestPW"
            assert user_after.password_hash != old_password_hash
            assert user_after.check_password("newpassword")

    def test_profile_post_incorrect_current_password(
        self, logged_in_client, app, test_user
    ):
        with app.app_context():
            profile_url = url_for("auth.profile")
            response = logged_in_client.post(
                profile_url,
                data={
                    "username": test_user.username,
                    "email": test_user.email,
                    "first_name": test_user.first_name,
                    "last_name": test_user.last_name,
                    "current_password": "wrongpassword",
                    "new_password": "newpassword",
                    "confirm_new_password": "newpassword",
                },
                follow_redirects=True,
            )

        assert response.status_code == 200
        assert b"Incorrect current password." in response.data
        assert (
            b"Password change failed. Please correct the errors below." in response.data
        )

    @patch("app.routes.auth.User.query")
    def test_profile_post_username_taken(
        self, mock_user_query_in_route, logged_in_client, app, test_user
    ):
        with app.app_context():
            existing_user_mock = MagicMock(spec=User)
            existing_user_mock.id = test_user.id + 1
            mock_user_query_in_route.filter.return_value.first.return_value = (
                existing_user_mock
            )
            profile_url = url_for("auth.profile")

            response = logged_in_client.post(
                profile_url,
                data={
                    "username": "takenuser",
                    "email": test_user.email,
                    "first_name": test_user.first_name,
                    "last_name": test_user.last_name,
                    "current_password": "",
                    "new_password": "",
                    "confirm_new_password": "",
                },
                follow_redirects=True,
            )

        assert response.status_code == 200
        assert b"Username already taken." in response.data
        assert (
            b"Profile update failed. Please correct the errors below." in response.data
        )
        mock_user_query_in_route.filter.assert_called()

    # --- Password Reset Request Tests ---
    @patch("app.routes.auth.send_password_reset_email")
    def test_request_reset_token_success(self, mock_send_email, client, app, test_user):
        with app.app_context():
            assert test_user.password_hash is not None
            request_url = url_for("auth.request_reset_token")
            response = client.post(
                request_url,
                data={"email": test_user.email},
                follow_redirects=True,
            )
        assert response.status_code == 200
        assert b"An email has been sent" in response.data
        mock_send_email.assert_called_once()
        assert mock_send_email.call_args[0][0].email == test_user.email

    def test_request_reset_token_email_not_found(self, client, app):
        with app.app_context():
            request_url = url_for("auth.request_reset_token")
            response = client.post(
                request_url,
                data={"email": "nonexistent@example.com"},
                follow_redirects=True,
            )
        assert response.status_code == 200
        assert b"There is no account with that email" in response.data

    @patch("app.routes.auth.User.verify_reset_password_token")
    def test_reset_token_get_valid_token(self, mock_verify_token, client, app):
        with app.app_context():
            dummy_user = User(
                id=123, username="resetuser_get", email="reset_get@example.com"
            )
            mock_verify_token.return_value = dummy_user
            reset_url = url_for("auth.reset_token", token="validtoken_get")
            response = client.get(reset_url)

        assert response.status_code == 200
        assert b"Reset Password" in response.data
        mock_verify_token.assert_called_once_with("validtoken_get")

    @patch("app.routes.auth.User.verify_reset_password_token")
    def test_reset_token_get_invalid_token(self, mock_verify_token, client, app):
        with app.app_context():
            mock_verify_token.return_value = None
            reset_url = url_for("auth.reset_token", token="invalidtoken_get")
            response = client.get(reset_url, follow_redirects=True)

        assert response.status_code == 200
        assert b"That is an invalid or expired token." in response.data
        assert b"Request Password Reset" in response.data
        mock_verify_token.assert_called_once_with("invalidtoken_get")

    @patch("app.routes.auth.User.verify_reset_password_token")
    @patch("app.routes.auth.db.session.commit")
    def test_reset_token_post_success(
        self, mock_db_commit, mock_verify_token, client, app):
        with app.app_context():
            user_to_reset = User(
                id=124, username="resetuser_post", email="reset_post@example.com"
            )
            user_to_reset.set_password("oldpassword_post")
            original_hash = user_to_reset.password_hash
            _db.session.add(user_to_reset)
            _db.session.commit()

            mock_db_commit.reset_mock()

            mock_verify_token.return_value = user_to_reset
            reset_url = url_for("auth.reset_token", token="validtoken_post")
            response = client.post(
                reset_url,
                data={"password": "newpassword_post", "password2": "newpassword_post"},
                follow_redirects=True,
            )
        assert response.status_code == 200
        assert b"Your password has been updated!" in response.data
        mock_verify_token.assert_called_once_with("validtoken_post")
        mock_db_commit.assert_called_once()

        assert user_to_reset.password_hash is not None
        assert user_to_reset.password_hash != original_hash
        assert user_to_reset.check_password("newpassword_post")

        with app.app_context():
            # This user might not actually be in the DB if the initial commit was mocked without side effect
            persisted_user_after_reset = _db.session.get(User, user_to_reset.id)
            if persisted_user_after_reset:
                _db.session.delete(persisted_user_after_reset)
                _db.session.commit()

    @patch("app.routes.auth.User.verify_reset_password_token")
    def test_reset_token_post_password_mismatch(self, mock_verify_token, client, app):
        with app.app_context():
            dummy_user = User(
                id=125,
                username="resetuser_mismatch",
                email="reset_mismatch@example.com",
            )
            mock_verify_token.return_value = dummy_user
            reset_url = url_for("auth.reset_token", token="validtoken_mismatch")
            response = client.post(
                reset_url,
                data={
                    "password": "newpassword_mismatch",
                    "password2": "mismatch_error",
                },
                follow_redirects=True,
            )
        assert response.status_code == 200
        assert b"Passwords must match." in response.data
