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
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'native_decimal': True}

    with app.app_context():
        db.create_all()

        # --- Role Setup ---

        # Create the Admin role if it doesn't exist (important for is_admin property)
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin', description='Administrator role')
            db.session.add(admin_role)
            

        # --- User Creation ---
        regular_user = User(username='testuser', email='test@example.com')
        regular_user.set_password('password')
        admin_user = User(username='adminuser', email='admin@example.com')
        admin_user.set_password('adminpassword')
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
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client 

# Helper to login 
def login(client, username, password):
    response = client.post(url_for('auth.login', _external=False), data=dict( # Use relative URL
        username=username,
        password=password
    ), follow_redirects=False) 

    assert response.status_code == 302, f"Login failed, status code: {response.status_code}"
    expected_location = url_for('main.product_list', _external=False)
    assert response.location.rstrip('/') == expected_location.rstrip('/'), \
           f"Expected redirect to {expected_location}, but got {response.location}"
    client.get(response.location)

# Helper function to log out
def logout(client):
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
            user_id_for_urls = regular_user.id

        # Generate relative paths for comparison
        login_url_path = url_for('auth.login', _external=False)
        routes_to_check = [
            url_for('admin.user_list', _external=False),
            url_for('admin.add_user', _external=False),
            url_for('admin.edit_user', user_id=user_id_for_urls, _external=False),
            url_for('admin.delete_user', user_id=user_id_for_urls, _external=False)
        ]

        for route in routes_to_check:
            response = test_client.get(route)
            assert response.status_code == 302, f"Route {route} did not redirect"
            assert response.location.startswith(login_url_path), \
                   f"Route {route} redirected to {response.location}, expected start with {login_url_path}"

    def test_admin_routes_non_admin(self, test_client):
        """Test accessing admin routes as non-admin redirects & flashes message."""

        login(test_client, 'testuser', 'password') 

        with test_client.application.app_context():
            regular_user = User.query.filter_by(username='testuser').first()
            assert regular_user is not None
            user_id_for_urls = regular_user.id

        # Generate relative paths
        expected_redirect_path = url_for('main.product_list', _external=False)
        routes_and_permissions = {
            url_for('admin.user_list', _external=False): 'view_users',
            url_for('admin.add_user', _external=False): 'manage_users',
            url_for('admin.edit_user', user_id=user_id_for_urls, _external=False): 'manage_users',
            url_for('admin.delete_user', user_id=user_id_for_urls, _external=False): 'manage_users'
        }

        for route, permission in routes_and_permissions.items():
            response = test_client.get(route, follow_redirects=False) # Check redirect first
            assert response.status_code == 302, f"Route {route} did not redirect for non-admin"
            assert response.location.rstrip('/') == expected_redirect_path.rstrip('/'), \
                f"Route {route} redirected to {response.location}, expected {expected_redirect_path}"

            # Check for flash message in session
            with test_client.session_transaction() as sess:
                 flashes = sess.get('_flashes', [])
                 expected_flash = ('danger', f'You do not have permission to access this resource ({permission}).')

                 assert expected_flash in flashes, \
                    f"Flash message check failed for route {route}. Expected '{expected_flash}', Got '{flashes}'"

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
        mock_user.username = 'newuser'
        mock_user_service.create_user.return_value = (mock_user, {})

        user_data = { 'username': 'newuser', 'email': 'new@example.com', 'password': 'newpassword', 'password2': 'newpassword', 'roles': [] }
        response = test_client.post(url_for('admin.add_user', _external=False), data=user_data, follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"

        # Check flash message after redirect
        redirect_response = test_client.get(response.location)


        # Check for both literal and HTML-escaped quotes
        expected_flash_text_raw = f'User "{mock_user.username}" created successfully!'
        expected_flash_text_literal = expected_flash_text_raw.encode()
        expected_flash_text_escaped_quot = expected_flash_text_raw.replace('"', '&quot;').encode()
        expected_flash_text_escaped_34 = expected_flash_text_raw.replace('"', '&#34;').encode() # Added check for &#34;

         # Assert that *either* the literal or escaped version is present
        assert (expected_flash_text_literal in redirect_response.data or
            expected_flash_text_escaped_quot in redirect_response.data or
            expected_flash_text_escaped_34 in redirect_response.data), \
            f"Expected flash message '{expected_flash_text_raw}' (literal or escaped with &quot; or &#34;) not found in response."
    

        mock_user_service.create_user.assert_called_once()
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_add_user_post_admin_validation_error(self, mock_user_service, test_client):
        """Test POST /admin/users/add as admin (validation error)."""

        login(test_client, 'adminuser', 'adminpassword')
        mock_user_service.create_user.return_value = (None, {'username': ['Username already taken']})

        user_data = { 'username': 'adminuser', 'email': 'new@example.com', 'password': 'newpassword', 'password2': 'newpassword', 'roles': [] }
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
             user_id_to_edit = regular_user.id

         # Mock the service call for update_user
        mock_updated_user = MagicMock(spec=User)
        mock_updated_user.username = 'testuser_edited' # Give mock a username for flash message
        mock_user_service.update_user.return_value = (mock_updated_user, {})

        edit_data = { 'username': 'testuser_edited', 'email': 'test_edited@example.com', 'frsit_name': '', 'last_name': '',  'password': '', 'password2': '', 'roles': []}
        response = test_client.post(url_for('admin.edit_user', user_id=user_id_to_edit, _external=False), data=edit_data, follow_redirects=False)

        assert response.status_code == 302, f"POST edit failed with status {response.status_code}"
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"

        redirect_response = test_client.get(response.location)

         



        # Check flash message after redirect
        expected_flash_text_raw = f'User "{mock_updated_user.username}" updated successfully!'
        expected_flash_text_literal = expected_flash_text_raw.encode()
        expected_flash_text_escaped_quot = expected_flash_text_raw.replace('"', '&quot;').encode()
        expected_flash_text_escaped_34 = expected_flash_text_raw.replace('"', '&#34;').encode() 

        assert (expected_flash_text_literal in redirect_response.data or
            expected_flash_text_escaped_quot in redirect_response.data or
            expected_flash_text_escaped_34 in redirect_response.data), \
            f"Expected flash message '{expected_flash_text_raw}' (literal or escaped with &quot; or &#34;) not found in response."

        # Verify service method was called correctly
        mock_user_service.update_user.assert_called_once()
        args, kwargs = mock_user_service.update_user.call_args
        assert args[0] == user_id_to_edit
        assert args[1]['username'] == 'testuser_edited'
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_edit_user_get_admin_not_found(self, mock_user_service, test_client):
        """Test GET /admin/users/edit/<id> for non-existent user."""

        login(test_client, 'adminuser', 'adminpassword')
        non_existent_user_id = 999
        mock_user_service.get_user_by_id.return_value = None

        response = test_client.get(url_for('admin.edit_user', user_id=non_existent_user_id, _external=False), follow_redirects=False)

        # The route should redirect if user not found
        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"


        # Check flash message after redirect
        redirect_response = test_client.get(response.location)
        assert b'User not found.' in redirect_response.data

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
            user_id_to_delete = regular_user.id

        mock_user_service.delete_user.return_value = True

        response = test_client.get(url_for('admin.delete_user', user_id=user_id_to_delete, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"

        # Check flash message after redirect
        redirect_response = test_client.get(response.location)
        assert b'User deleted successfully!' in redirect_response.data

        mock_user_service.delete_user.assert_called_once_with(user_id_to_delete)
        logout(test_client)

    @patch('app.routes.admin.UserService')
    def test_delete_self_fail(self, mock_user_service, test_client):
        """Test GET /admin/users/delete/<id> trying to delete self."""

        login(test_client, 'adminuser', 'adminpassword')
        with test_client.application.app_context():
            admin_user = User.query.filter_by(username='adminuser').first()
            assert admin_user is not None
            admin_user_id = admin_user.id

        response = test_client.get(url_for('admin.delete_user', user_id=admin_user_id, _external=False), follow_redirects=False)

        assert response.status_code == 302
        expected_location = url_for('admin.user_list', _external=False)
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"


        # Check flash message after redirect
        redirect_response = test_client.get(response.location)
        assert b'You cannot delete yourself.' in redirect_response.data

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
        assert response.location.rstrip('/') == expected_location.rstrip('/'), f"Redirect failed: expected {expected_location}, got {response.location}"

        # Check flash message after redirect
        redirect_response = test_client.get(response.location)
        # The route flashes 'User not found. or error deleting user.'
        assert b'User not found. or error deleting user.' in redirect_response.data

        mock_user_service.delete_user.assert_called_once_with(non_existent_user_id)
        logout(test_client)











