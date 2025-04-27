import pytest
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.role import Role
from unittest.mock import patch, MagicMock

@pytest.fixture(scope='module')
def test_app():
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost' # Needed for url_for generation consistency
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for tests

    with app.app_context():
        db.create_all()

        # --- Role Setup ---

        # Create the Admin role if it doesn't exist (important for is_admin property)
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator role')
            db.session.add(admin_role)
            db.session.commit() # Commit role first if needed, or commit all at the end

        # --- User Creation ---
        regular_user = User(username='testuser', email='test@example.com')
        regular_user.set_password('password')

        admin_user = User(username='adminuser', email='admin@example.com')
        admin_user.set_password('adminpassword')

        # --- Associate Role with Admin User ---
        admin_user.roles.append(admin_role)

        # --- Add users to session and commit ---
        db.session.add_all([regular_user, admin_user])
        db.session.commit()

        # Verify users were created correctly and admin has the role
        retrieved_regular = User.query.filter_by(username='testuser').first()
        retrieved_admin = User.query.filter_by(username='adminuser').first()
        assert retrieved_regular is not None
        assert retrieved_admin is not None
        assert retrieved_admin.has_role('Admin') is True
        assert retrieved_admin.is_admin is True
        assert retrieved_regular.is_admin is False

        yield app
        # Cleanup typically handled by ending the context with in-memory db

# Fixture for the test client - function scope ensures clean state
@pytest.fixture(scope='function')
def test_client(test_app):
    with test_app.app_context():
        yield test_app.test_client()

# Helper to login - CORRECTED ASSERTION
def login(client, username, password):
    response = client.post(url_for('auth.login', _external=False), data=dict( # Use relative URL
        username=username,
        password=password
    ), follow_redirects=False) # Don't follow redirect yet

    assert response.status_code == 302, f"Login failed, status code: {response.status_code}"
    # Compare response.location (relative path) with relative url_for
    expected_location = url_for('main.product_list', _external=False)
    assert response.location == expected_location, f"Expected redirect to {expected_location}, but got {response.location}"

    # Manually follow the redirect to complete the login process state
    client.get(response.location)


# Helper function to log out
def logout(client):
    # Ensure url_for generates relative path if needed
    return client.get(url_for('auth.logout', _external=False), follow_redirects=True)

# --- Test Class for Admin Routes ---
class TestAdminRoutes:

    # Use function scope fixture to ensure app context for each test method
    @pytest.fixture(autouse=True)
    def setup_app_context(self, test_app):
        with test_app.app_context():
            yield

    # === Access Control Tests ===

    def test_admin_routes_unauthenticated(self, test_client):
        """Test accessing admin routes without being logged in redirects to login."""
        with test_client.application.app_context():
            regular_user = User.query.filter_by(username='testuser').first()
            assert regular_user is not None, "Regular user not found in fixture"

        # Generate relative paths for comparison
        login_url_path = url_for('auth.login', _external=False)
        routes_to_check = [
            url_for('admin.user_list', _external=False),
            url_for('admin.add_user', _external=False),
            url_for('admin.edit_user', user_id=regular_user.id, _external=False),
            url_for('admin.delete_user', user_id=regular_user.id, _external=False)
        ]

        for route in routes_to_check:
            response = test_client.get(route)
            assert response.status_code == 302, f"Route {route} did not redirect"
            # Check if the redirect target starts with the login path
            assert response.location.startswith(login_url_path), \
                   f"Route {route} redirected to {response.location}, expected start with {login_url_path}"

    def test_admin_routes_non_admin(self, test_client):
        """Test accessing admin routes as non-admin redirects & flashes message."""
        login(test_client, 'testuser', 'password') # Use corrected login helper

        with test_client.application.app_context():
            regular_user = User.query.filter_by(username='testuser').first()
            assert regular_user is not None

        # Generate relative paths
        expected_redirect_path = url_for('main.product_list', _external=False)
        routes_to_check = [
            url_for('admin.user_list', _external=False),
            url_for('admin.add_user', _external=False),
            url_for('admin.edit_user', user_id=regular_user.id, _external=False),
            url_for('admin.delete_user', user_id=regular_user.id, _external=False)
        ]

        for route in routes_to_check:
            response = test_client.get(route, follow_redirects=False) # Check redirect first
            assert response.status_code == 302, f"Route {route} did not redirect for non-admin"
            assert response.location == expected_redirect_path, \
                   f"Route {route} redirected to {response.location}, expected {expected_redirect_path}"

            # Check for flash message in session
            with test_client.session_transaction() as sess:
                 flashes = sess.get('_flashes', [])
                 expected_flash = ('danger', 'You need to be an admin to access this page.')
                 assert expected_flash in flashes, f"Flash message check failed for route {route}"

        logout(test_client)

    # === User List Tests ===

    def test_user_list_get_admin(self, test_client):
        """Test GET /admin/users as admin."""
        login(test_client, 'adminuser', 'adminpassword')
        response = test_client.get(url_for('admin.user_list', _external=False))
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        assert b'User Management' in response.data
        assert b'adminuser' in response.data
        assert b'testuser' in response.data
        logout(test_client)

    # === Add User Tests ===

    def test_add_user_get_admin(self, test_client):
        """Test GET /admin/users/add as admin."""
        login(test_client, 'adminuser', 'adminpassword')
        response = test_client.get(url_for('admin.add_user', _external=False))
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        assert b'Add New User' in response.data
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_add_user_post_admin_success(self, mock_user_service, test_client):
        """Test POST /admin/users/add as admin (success)."""
        login(test_client, 'adminuser', 'adminpassword')
        mock_user = MagicMock(spec=User)
        mock_user_service.create_user.return_value = (mock_user, {})

        user_data = { 'username': 'newuser', 'email': 'new@example.com', 'password': 'newpassword', 'password2': 'newpassword' }
        response = test_client.post(url_for('admin.add_user', _external=False), data=user_data, follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('success', 'User created successfully!') in sess.get('_flashes', [])

        mock_user_service.create_user.assert_called_once()
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_add_user_post_admin_validation_error(self, mock_user_service, test_client):
        """Test POST /admin/users/add as admin (validation error)."""
        login(test_client, 'adminuser', 'adminpassword')
        mock_user_service.create_user.return_value = (None, {'username': 'Username already taken'})

        user_data = { 'username': 'adminuser', 'email': 'new@example.com', 'password': 'newpassword', 'password2': 'newpassword' }
        response = test_client.post(url_for('admin.add_user', _external=False), data=user_data, follow_redirects=False)

        assert response.status_code == 200, f"Expected 200 OK on validation error, got {response.status_code}"
        assert b'Username already taken' in response.data
        mock_user_service.create_user.assert_called_once()
        logout(test_client)

    # === Edit User Tests ===

    def test_edit_user_get_admin(self, test_client):
        """Test GET /admin/users/edit/<id> as admin."""
        login(test_client, 'adminuser', 'adminpassword')
        with test_client.application.app_context():
            regular_user = User.query.filter_by(username='testuser').first()
            assert regular_user is not None
        response = test_client.get(url_for('admin.edit_user', user_id=regular_user.id, _external=False))
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        assert b'Edit User: testuser' in response.data
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_edit_user_post_admin_success(self, mock_user_service, test_client):
        """Test POST /admin/users/edit/<id> as admin (success)."""
        login(test_client, 'adminuser', 'adminpassword')
        with test_client.application.app_context():
             regular_user = User.query.filter_by(username='testuser').first()
             assert regular_user is not None

        mock_service_user = MagicMock(spec=User)
        mock_user_service.get_user_by_id.return_value = mock_service_user
        mock_user_service.update_user.return_value = (mock_service_user, {})

        edit_data = { 'username': 'testuser_edited', 'email': 'test_edited@example.com', 'password': '', 'password2': ''}
        response = test_client.post(url_for('admin.edit_user', user_id=regular_user.id, _external=False), data=edit_data, follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('success', 'User updated successfully!') in sess.get('_flashes', [])

        mock_user_service.update_user.assert_called_once()
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_edit_user_get_admin_not_found(self, mock_user_service, test_client):
        """Test GET /admin/users/edit/<id> for non-existent user."""
        login(test_client, 'adminuser', 'adminpassword')
        non_existent_user_id = 999
        mock_user_service.get_user_by_id.return_value = None

        response = test_client.get(url_for('admin.edit_user', user_id=non_existent_user_id, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('danger', 'User not found.') in sess.get('_flashes', [])

        mock_user_service.get_user_by_id.assert_called_once_with(non_existent_user_id)
        logout(test_client)


    # === Delete User Tests ===

    @patch('app.routes.admin.UserService')
    def test_delete_user_success(self, mock_user_service, test_client):
        """Test GET /admin/users/delete/<id> as admin (success)."""
        login(test_client, 'adminuser', 'adminpassword')
        with test_client.application.app_context():
            regular_user = User.query.filter_by(username='testuser').first()
            assert regular_user is not None
        mock_user_service.delete_user.return_value = True

        response = test_client.get(url_for('admin.delete_user', user_id=regular_user.id, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('success', 'User deleted successfully!') in sess.get('_flashes', [])

        mock_user_service.delete_user.assert_called_once_with(regular_user.id)
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_delete_self_fail(self, mock_user_service, test_client):
        """Test GET /admin/users/delete/<id> trying to delete self."""
        login(test_client, 'adminuser', 'adminpassword')
        with test_client.application.app_context():
            admin_user = User.query.filter_by(username='adminuser').first()
            assert admin_user is not None

        response = test_client.get(url_for('admin.delete_user', user_id=admin_user.id, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('danger', 'You cannot delete yourself.') in sess.get('_flashes', [])

        mock_user_service.delete_user.assert_not_called()
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_delete_user_not_found(self, mock_user_service, test_client):
        """Test GET /admin/users/delete/<id> for non-existent user."""
        login(test_client, 'adminuser', 'adminpassword')
        non_existent_user_id = 999
        mock_user_service.delete_user.return_value = False

        response = test_client.get(url_for('admin.delete_user', user_id=non_existent_user_id, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location == expected_location, f"Redirect failed: expected {expected_location}, got {response.location}"

        with test_client.session_transaction() as sess:
            assert ('danger', 'User not found.') in sess.get('_flashes', [])

        mock_user_service.delete_user.assert_called_once_with(non_existent_user_id)
        logout(test_client)











