import pytest
from unittest.mock import patch, MagicMock
from app.models import Role, Permission
from app.services.role_service import RoleService
from app import create_app

@pytest.fixture(scope="module")
def test_app():

    """Fixture to set up the Flask app for testing (needed for context)."""
    app = create_app("testing")  
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    yield app


@pytest.fixture(scope="function", autouse=True)  
def app_context(test_app):

    """Fixture to push an application context for each test."""

    with test_app.app_context():  
        yield


@pytest.fixture
def mock_role():
    """Fixture to create a basic mock Role object."""
    role = MagicMock(spec=Role)
    role.id = 1
    role.name = "Test Role"
    # Initialize permissions as an empty list for assignment later
    role.permissions = []
    return role


@pytest.fixture
def mock_permissions():
    """Fixture to create a list of basic mock Permission objects."""
    perm1 = MagicMock(spec=Permission)
    perm1.id = 101
    perm1.name = "edit_thing"
    perm2 = MagicMock(spec=Permission)
    perm2.id = 102
    perm2.name = "delete_thing"
    return [perm1, perm2]


# --- Test Class for RoleService ---


class TestRoleService:

    # === Test get_all_roles ===

    @patch("app.services.role_service.Role")
    def test_get_all_roles_success(self, MockRole):
        """Test get_all_roles returns roles successfully."""
        mock_roles_list = [MagicMock(spec=Role), MagicMock(spec=Role)]
        # Configure the mock chain: Role.query.order_by().all()
        MockRole.query.order_by.return_value.all.return_value = mock_roles_list

        roles = RoleService.get_all_roles()

        assert roles == mock_roles_list
        MockRole.query.order_by.assert_called_once_with(MockRole.name)
        MockRole.query.order_by.return_value.all.assert_called_once()
    

    @patch("app.services.role_service.Role")
    @patch("app.services.role_service.current_app")
    def test_get_all_roles_exception(self, mock_current_app, MockRole):

        """Test get_all_roles handles exceptions and returns empty list."""

        test_exception = Exception("DB connection failed")
        # Configure the mock chain to raise an exception
        MockRole.query.order_by.return_value.all.side_effect = test_exception

        roles = RoleService.get_all_roles()

        assert roles == []
        MockRole.query.order_by.assert_called_once_with(MockRole.name)
        MockRole.query.order_by.return_value.all.assert_called_once()
        # Check if logger was called (optional, but good practice)
        mock_current_app.logger.error.assert_called_once()
        # Check if the exception message is somewhere in the log call args
        args, kwargs = mock_current_app.logger.error.call_args
        assert "Error fetching all roles" in args[0]
        assert str(test_exception) in args[0]
        assert kwargs.get("exc_info") is True

    # === Test get_role_by_id ===

    @patch("app.services.role_service.db")
    def test_get_role_by_id_found(self, mock_db, mock_role):
        """Test get_role_by_id returns a role when found."""
        mock_db.session.get.return_value = mock_role
        role_id_to_find = mock_role.id

        role = RoleService.get_role_by_id(role_id_to_find)

        assert role == mock_role
        mock_db.session.get.assert_called_once_with(Role, role_id_to_find)

    @patch("app.services.role_service.db")
    def test_get_role_by_id_not_found(self, mock_db):
        """Test get_role_by_id returns None when role is not found."""
        mock_db.session.get.return_value = None
        role_id_to_find = 999

        role = RoleService.get_role_by_id(role_id_to_find)

        assert role is None
        mock_db.session.get.assert_called_once_with(Role, role_id_to_find)

    @patch("app.services.role_service.db")
    @patch("app.services.role_service.current_app")
    def test_get_role_by_id_exception(self, mock_current_app, mock_db):
        """Test get_role_by_id handles exceptions and returns None."""
        test_exception = Exception("DB error")
        mock_db.session.get.side_effect = test_exception
        role_id_to_find = 1

        role = RoleService.get_role_by_id(role_id_to_find)

        assert role is None
        mock_db.session.get.assert_called_once_with(Role, role_id_to_find)
        mock_current_app.logger.error.assert_called_once()
        args, kwargs = mock_current_app.logger.error.call_args
        assert f"Error fetching role ID {role_id_to_find}" in args[0]
        assert str(test_exception) in args[0]
        assert kwargs.get("exc_info") is True

    # === Test update_role_permissions ===

    @patch(
        "app.services.role_service.RoleService.get_role_by_id"
    )  # Patch the method within the class
    def test_update_role_permissions_role_not_found(self, mock_get_role):
        """Test update fails gracefully if role_id is invalid."""
        mock_get_role.return_value = None
        role_id = 999
        permission_ids = [1, 2]

        result_role, error_message = RoleService.update_role_permissions(
            role_id, permission_ids
        )

        assert result_role is None
        assert error_message == "Role not found."
        mock_get_role.assert_called_once_with(role_id)

    @patch("app.services.role_service.Permission")
    @patch("app.services.role_service.db")
    @patch("app.services.role_service.RoleService.get_role_by_id")
    @patch("app.services.role_service.current_app")
    def test_update_role_permissions_success_with_ids(
        self,
        mock_current_app,
        mock_get_role,
        mock_db,
        MockPermission,
        mock_role,
        mock_permissions,
    ):
        """Test updating permissions with a list of valid IDs."""
        role_id = mock_role.id
        initial_permissions = [MagicMock(spec=Permission)]
        mock_role.permissions = initial_permissions[:]  # Assign initial state
        mock_get_role.return_value = mock_role

        # Configure Permission query mock
        permission_ids = [p.id for p in mock_permissions]
        MockPermission.query.filter.return_value.all.return_value = mock_permissions

        result_role, error_message = RoleService.update_role_permissions(
            role_id, permission_ids
        )

        assert error_message is None
        assert result_role == mock_role
        # IMPORTANT: Check that the actual permissions list on the mock role was updated
        assert result_role.permissions == mock_permissions
        mock_get_role.assert_called_once_with(role_id)
        # Check that the permission query was called correctly
        MockPermission.query.filter.assert_called_once()
        MockPermission.query.filter.return_value.all.assert_called_once()
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()
        mock_current_app.logger.info.assert_called_once()

    @patch("app.services.role_service.Permission")
    @patch("app.services.role_service.db")
    @patch("app.services.role_service.RoleService.get_role_by_id")
    @patch("app.services.role_service.current_app")
    def test_update_role_permissions_success_empty_list(
        self, mock_current_app, mock_get_role, mock_db, MockPermission, mock_role
    ):
        """Test updating permissions with an empty list (clearing permissions)."""
        role_id = mock_role.id
        initial_permissions = [MagicMock(spec=Permission)]
        mock_role.permissions = initial_permissions[:]  # Assign initial state
        mock_get_role.return_value = mock_role

        permission_ids = []  # Empty list

        result_role, error_message = RoleService.update_role_permissions(
            role_id, permission_ids
        )

        assert error_message is None
        assert result_role == mock_role
        # IMPORTANT: Check permissions list is now empty
        assert result_role.permissions == []
        mock_get_role.assert_called_once_with(role_id)
        # Permission query should NOT be called when permission_ids is empty
        MockPermission.query.filter.assert_not_called()
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_not_called()
        mock_current_app.logger.info.assert_called_once()

    @patch("app.services.role_service.Permission")
    @patch("app.services.role_service.db")
    @patch("app.services.role_service.RoleService.get_role_by_id")
    @patch("app.services.role_service.current_app")
    def test_update_role_permissions_db_exception(
        self,
        mock_current_app,
        mock_get_role,
        mock_db,
        MockPermission,
        mock_role,
        mock_permissions,
    ):
        """Test update handles database commit errors."""
        role_id = mock_role.id
        mock_role.permissions = []  # Start empty for simplicity
        mock_get_role.return_value = mock_role

        # Configure Permission query mock
        permission_ids = [p.id for p in mock_permissions]
        MockPermission.query.filter.return_value.all.return_value = mock_permissions

        # Configure commit mock to raise exception
        test_exception = Exception("Commit failed")
        mock_db.session.commit.side_effect = test_exception

        result_role, error_message = RoleService.update_role_permissions(
            role_id, permission_ids
        )

        assert result_role == mock_role  # Should still return the role object
        assert error_message == "Database error updating permissions."
        # Check permissions were assigned before commit attempt
        assert result_role.permissions == mock_permissions
        mock_get_role.assert_called_once_with(role_id)
        MockPermission.query.filter.assert_called_once()
        MockPermission.query.filter.return_value.all.assert_called_once()
        # Check commit was attempted and rollback occurred
        mock_db.session.commit.assert_called_once()
        mock_db.session.rollback.assert_called_once()
        # Check logger
        mock_current_app.logger.error.assert_called_once()
        args, kwargs = mock_current_app.logger.error.call_args
        assert f"Error updating permissions for role ID {role_id}" in args[0]
        assert str(test_exception) in args[0]
        assert kwargs.get("exc_info") is True
        mock_current_app.logger.info.assert_not_called()  # Info log should not happen on error
