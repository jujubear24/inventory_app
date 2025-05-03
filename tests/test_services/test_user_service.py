import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from app.services.user_service import UserService
from app.models.user import User
from app.models.role import Role 
# --- Fixtures ---

@pytest.fixture
def mock_db_session(mocker):
    """Fixture to mock db.session"""
    mock_session = MagicMock()
    mocker.patch('app.services.user_service.db.session', mock_session)
    # Mock db.session.get specifically
    mock_session.get = MagicMock()
    return mock_session

@pytest.fixture
def mock_user_query(mocker):
    """Fixture to mock User.query"""

    patched_query_mock = mocker.patch('app.services.user_service.User.query')
    
    patched_query_mock.order_by.return_value.all.return_value = []
    patched_query_mock.filter.return_value.filter.return_value.first.return_value = None
    patched_query_mock.filter.return_value.first.return_value = None
    return patched_query_mock

@pytest.fixture
def mock_oauth_query(mocker):
    """Fixture to mock OAuth.query"""
    mock_oquery = MagicMock()
    mocker.patch('app.services.user_service.OAuth.query', mock_oquery)
    # Mock chained methods
    mock_oquery.filter_by.return_value.delete.return_value = 1 # Simulate 1 record deleted
    return mock_oquery


@pytest.fixture
def mock_logger(mocker):
    """Fixture to mock current_app.logger"""
    mock_log = MagicMock()
    mocker.patch('app.services.user_service.current_app.logger', mock_log)
    return mock_log

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample data for creating a user"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'first_name': 'Test',
        'last_name': 'User',
        'roles': ['user'] # Assuming roles are handled like this
    }

@pytest.fixture
def existing_user() -> User:
    """Sample existing user object"""
    user = User(id=1, username='existing', email='exists@example.com')
    # Mock the set_password method if it's used internally by other methods being tested
    user.set_password = MagicMock()
    return user

@pytest.fixture
def mock_role_query(mocker):
    """Fixture to mock Role.query"""
    # Patch Role.query where it's used in user_service
    mock_query = mocker.patch('app.services.user_service.Role.query')
    # Default behavior (can be overridden in tests)
    mock_query.filter.return_value.all.return_value = []
    return mock_query

# --- Test User Service Format ---
class TestUserServiceFormatValidation:

    @pytest.mark.parametrize("test_id, data, is_new, expected_errors", [
        ("valid_new", {'username': 'new', 'email': 'new@e.com', 'password': 'password123'}, True, {}),
        ("missing_username", {'email': 'new@e.com', 'password': 'password123'}, True, {'username': 'Username is required'}),
        ("missing_email", {'username': 'new', 'password': 'password123'}, True, {'email': 'Email is required'}),
        ("missing_password_new", {'username': 'new', 'email': 'new@e.com'}, True, {'password': 'Password is required'}),
        ("password_not_missing_update", {'username': 'upd', 'email': 'upd@e.com'}, False, {}), # Password not required for update
        ("short_password", {'username': 'new', 'email': 'new@e.com', 'password': 'short'}, True, {'password': 'Password must be at least 8 characters'}),
        # Add more cases for format checks as needed
    ])
    def test_validate_user_format(self, test_id, data, is_new, expected_errors):
         errors = UserService._validate_user_format(data, is_new=is_new)
         assert errors == expected_errors, f"Test ID: {test_id}"





# --- Test Class ---
@pytest.mark.usefixtures("app_context")
class TestUserService:

    # --- get_all_users ---
    def test_get_all_users(self, mock_user_query):
        mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
        mock_user_query.order_by.return_value.all.return_value = mock_users
        
        users = UserService.get_all_users()
        
        assert users == mock_users
        mock_user_query.order_by.assert_called_once_with(User.username)
        mock_user_query.order_by.return_value.all.assert_called_once()

    # --- get_user_by_id ---
    def test_get_user_by_id_found(self, mock_db_session, existing_user):
        mock_db_session.get.return_value = existing_user
        user_id = 1
        
        user = UserService.get_user_by_id(user_id)
        
        assert user == existing_user
        mock_db_session.get.assert_called_once_with(User, user_id)

    def test_get_user_by_id_not_found(self, mock_db_session):
        mock_db_session.get.return_value = None
        user_id = 99
        
        user = UserService.get_user_by_id(user_id)
        
        assert user is None
        mock_db_session.get.assert_called_once_with(User, user_id)

    # --- create_user ---
    @patch('app.services.user_service.UserService.validate_user_data', return_value={}) # Mock validation success
    @patch('app.services.user_service.User') # Mock the User class constructor
    def test_create_user_success(self, mock_User_class, mock_validate, mock_db_session, mock_role_query, sample_user_data):
        mock_instance = mock_User_class.return_value
        mock_instance.set_password = MagicMock() # Mock the method on the instance

         # --- Mock Role Query Result ---
        mock_admin_role = MagicMock(spec=Role, name='AdminRole') # Create a mock Role object

        mock_admin_role._sa_instance_state = MagicMock()

        mock_role_query.filter.return_value.all.return_value = [mock_admin_role]

        user, errors = UserService.create_user(sample_user_data)

        assert user is not None
        assert errors == {}
        mock_validate.assert_called_once_with(sample_user_data, is_new=True)
        mock_User_class.assert_called_once_with(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name']
        )
        mock_instance.set_password.assert_called_once_with(sample_user_data['password'])

        # --- Assert Role Query and Assignment ---
        mock_role_query.filter.assert_called_once() # Check that Role.query.filter was called

        mock_role_query.filter.return_value.all.assert_called_once() # Check .all() was called
        assert list(mock_instance.roles) == [mock_admin_role] # Check the *mock Role object* was assigned


        mock_db_session.add.assert_called_once_with(mock_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_not_called()

    @patch('app.services.user_service.UserService.validate_user_data', return_value={'username': 'Required'})
    def test_create_user_validation_error(self, mock_validate, mock_db_session, sample_user_data):
        user, errors = UserService.create_user(sample_user_data)

        assert user is None
        assert errors == {'username': 'Required'}
        mock_validate.assert_called_once_with(sample_user_data, is_new=True)
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()

    @patch('app.services.user_service.UserService.validate_user_data', return_value={})
    @patch('app.services.user_service.User')
    def test_create_user_db_error(self, mock_User_class, mock_validate, mock_db_session, mock_logger, sample_user_data):
        # Simulate a DB error during commit
        mock_db_session.commit.side_effect = Exception("DB Unique constraint failed")
        mock_instance = mock_User_class.return_value
        mock_instance.set_password = MagicMock()

        user, errors = UserService.create_user(sample_user_data)

        assert user is None
        assert 'database' in errors
        assert "DB Unique constraint failed" in errors['database']
        mock_db_session.add.assert_called_once_with(mock_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_called_once() # Crucial check for coverage
        mock_logger.error.assert_called_once() # Check if logger was called

    # --- update_user ---
    @patch('app.services.user_service.UserService.validate_user_data', return_value={})
    def test_update_user_success(self, mock_validate, mock_db_session, mock_role_query, existing_user):
        user_id = existing_user.id
        update_data = {'first_name': 'Updated', 'roles': ['admin']}
        mock_db_session.get.return_value = existing_user

        # --- Mock Role Query Result ---
        mock_admin_role = MagicMock(spec=Role, name='AdminRole')

        mock_admin_role._sa_instance_state = MagicMock()

        mock_role_query.filter.return_value.all.return_value = [mock_admin_role]

        user, errors = UserService.update_user(user_id, update_data)

        assert user is not None
        assert errors == {}
        assert user.first_name == 'Updated' # Check field updated

        # --- Assert Role Query and Assignment ---
        mock_role_query.filter.assert_called_once() # Check Role.query.filter called
        mock_role_query.filter.return_value.all.assert_called_once() # Check .all() called
        assert list(user.roles) == [mock_admin_role] # Check mock Role object assigned

        assert user.set_password.call_count == 0 # Password not updated
        mock_validate.assert_called_once_with(update_data, user_id=user_id, is_new=False)
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_not_called()

    @patch('app.services.user_service.UserService.validate_user_data', return_value={})
    def test_update_user_with_password(self, mock_validate, mock_db_session, existing_user):
        user_id = existing_user.id
        update_data = {'password': 'newpassword123'}
        mock_db_session.get.return_value = existing_user

        user, errors = UserService.update_user(user_id, update_data)

        assert user is not None
        assert errors == {}
        user.set_password.assert_called_once_with('newpassword123') # Check password update
        mock_db_session.commit.assert_called_once()

    def test_update_user_not_found(self, mock_db_session):
        user_id = 99
        update_data = {'first_name': 'Updated'}
        mock_db_session.get.return_value = None # Simulate user not found

        user, errors = UserService.update_user(user_id, update_data)

        assert user is None
        assert errors == {'error': 'User not found'}
        mock_db_session.get.assert_called_once_with(User, user_id)
        mock_db_session.commit.assert_not_called()

    @patch('app.services.user_service.UserService.validate_user_data', return_value={'email': 'Taken'})
    def test_update_user_validation_error(self, mock_validate, mock_db_session, existing_user):
        user_id = existing_user.id
        update_data = {'email': 'other@example.com'}
        mock_db_session.get.return_value = existing_user

        user, errors = UserService.update_user(user_id, update_data)

        assert user is None
        assert errors == {'email': 'Taken'}
        mock_validate.assert_called_once_with(update_data, user_id=user_id, is_new=False)
        mock_db_session.commit.assert_not_called()

    @patch('app.services.user_service.UserService.validate_user_data', return_value={})
    def test_update_user_db_error(self, mock_validate, mock_db_session, mock_logger, existing_user):
        user_id = existing_user.id
        update_data = {'first_name': 'Updated'}
        mock_db_session.get.return_value = existing_user
        mock_db_session.commit.side_effect = Exception("DB Error on update") # Simulate DB error

        user, errors = UserService.update_user(user_id, update_data)

        assert user is None
        assert 'database' in errors
        assert "DB Error on update" in errors['database']
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_called_once() # Crucial check for coverage
        # mock_logger.error.assert_called_once() # Check logging if applicable in your actual code

    # --- delete_user ---
    def test_delete_user_success(self, mock_db_session, mock_oauth_query, mock_logger, existing_user):
        user_id = existing_user.id
        mock_db_session.get.return_value = existing_user

        result = UserService.delete_user(user_id)

        assert result is True
        mock_db_session.get.assert_called_once_with(User, user_id)
        mock_oauth_query.filter_by.assert_called_once_with(user_id=user_id) # Check OAuth deletion
        mock_oauth_query.filter_by.return_value.delete.assert_called_once()
        mock_db_session.flush.assert_called_once() # Check flush call
        mock_db_session.delete.assert_called_once_with(existing_user)
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_not_called()
        mock_logger.info.assert_called_once() # Check info log

    def test_delete_user_not_found(self, mock_db_session, mock_logger):
        user_id = 99
        mock_db_session.get.return_value = None # Simulate user not found

        result = UserService.delete_user(user_id)

        assert result is False
        mock_db_session.get.assert_called_once_with(User, user_id)
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
        mock_logger.warning.assert_called_once() # Check warning log

    def test_delete_user_db_error_on_commit(self, mock_db_session, mock_oauth_query, mock_logger, existing_user):
        user_id = existing_user.id
        mock_db_session.get.return_value = existing_user
        mock_db_session.commit.side_effect = Exception("Commit failed") # Simulate error

        result = UserService.delete_user(user_id)

        assert result is False
        mock_db_session.rollback.assert_called_once() # Crucial check for coverage
        mock_logger.error.assert_called_once() # Check error log

    def test_delete_user_db_error_on_oauth_delete(self, mock_db_session, mock_oauth_query, mock_logger, existing_user):
        user_id = existing_user.id
        mock_db_session.get.return_value = existing_user
        # Simulate error during OAuth delete
        mock_oauth_query.filter_by.return_value.delete.side_effect = Exception("OAuth delete failed") 

        result = UserService.delete_user(user_id)

        assert result is False
        mock_db_session.rollback.assert_called_once() # Crucial check for coverage
        mock_logger.error.assert_called_once() # Check error log
        mock_db_session.delete.assert_not_called() # Should fail before user delete
        mock_db_session.commit.assert_not_called() # Should fail before commit

    # --- validate_user_data ---
    # Use parametrize for cleaner validation tests
    @pytest.mark.parametrize("test_id, data, user_id, is_new, expected_errors, existing_user_mock", [
        ("username_taken_new", {'username': 'taken', 'email': 'new@e.com', 'password': 'password123'}, None, True, {'username': 'Username already taken'}, User(username='taken')),
        ("email_taken_new", {'username': 'new', 'email': 'taken@e.com', 'password': 'password123'}, None, True, {'email': 'Email already registered'}, User(email='taken@e.com')),
        ("valid_update_no_conflict", {'username': 'updated', 'email': 'update@e.com'}, 1, False, {}, None), # Test no conflict found
        ("username_taken_update_diff_user", {'username': 'taken', 'email': 'update@e.com'}, 1, False, {'username': 'Username already taken'}, User(id=2, username='taken')),
        ("username_not_taken_update_same_user", {'username': 'me', 'email': 'update@e.com'}, 1, False, {}, None), # Test no conflict found for own username
        ("email_taken_update_diff_user", {'username': 'update', 'email': 'taken@e.com'}, 1, False, {'email': 'Email already registered'}, User(id=2, email='taken@e.com')),
        ("email_not_taken_update_same_user", {'username': 'update', 'email': 'me@e.com'}, 1, False, {}, None), # Test no conflict found for own email
    ])

    def test_validate_user_data_uniqueness(self, test_id, data, user_id, is_new, expected_errors, existing_user_mock, mock_user_query):
        

        mock_user_query.reset_mock()

        # Default setup: query returns None
        default_return_mock = MagicMock()
        default_return_mock.first.return_value = None
        default_return_mock.filter.return_value.first.return_value = None

        def query_side_effect(*args, **kwargs):
            filter_clause = args[0]
            target_attr = None
            try:
                # Basic check for column name being filtered
                if hasattr(filter_clause.left, 'key'):
                    target_attr = filter_clause.left.key
            except AttributeError: 
                pass 

            print(f"--- DEBUG [side_effect]: Filtering on attribute: {target_attr}")

            # Prepare the mock chain for the next call (.filter() or .first())
            mock_chain = MagicMock()
            should_find_user = False

            # If a mock user should be found for *this specific attribute*
            if existing_user_mock:
                if target_attr == 'username' and getattr(existing_user_mock, 'username', None) is not None:
                    should_find_user = True
                    print("--- DEBUG [side_effect]: Mock has relevant USERNAME. Setting should_find_user=True") # DEBUG

                elif target_attr == 'email' and getattr(existing_user_mock, 'email', None) is not None:
                    should_find_user = True
                    print("--- DEBUG [side_effect]: Mock has relevant EMAIL. Setting should_find_user=True") # DEBUG

            
            if should_find_user:
                print(f"--- DEBUG [side_effect]: Configuring chain to return: {existing_user_mock}")
                mock_chain.first.return_value = existing_user_mock
                mock_chain.filter.return_value.first.return_value = existing_user_mock

            else:
                # Configure this chain step to ultimately return None
                mock_chain.first.return_value = None
                mock_chain.filter.return_value.first.return_value = None

            return mock_chain # Return mock configured for this filter call
        
        mock_user_query.filter.side_effect = query_side_effect
        errors = UserService.validate_user_data(data, user_id=user_id, is_new=is_new)

        assert errors == expected_errors, f"Test ID: {test_id}"


    # def test_validate_user_data(self, test_id, data, user_id, is_new, expected_errors, existing_user_mock, mock_user_query):
    #     """Configure the mock based on whether a user should be 'found'"""

    #     mock_user_query.reset_mock()
    #     mock_user_query.filter.return_value.first.return_value = None
    #     mock_user_query.filter.return_value.filter.return_value.first.return_value = None

    #     # Set up side effect to simulate conditional query results
    #     def query_side_effect(*args, **kwargs):
    #         # Get the filter clause (simplistic check)
    #         filter_clause = args[0]
    #         target_attr = None
    #         try:
    #             if hasattr(filter_clause.left, 'key'):
    #                 target_attr = filter_clause.left.key
    #         except AttributeError:
    #              pass # Ignore complex clauses for this simple mock

    #         print(f"--- DEBUG [validate_mock]: test_id={test_id}, target_attr={target_attr}") 

    #         # Assume we chain .filter().first()
    #         mock_chain = MagicMock()

    #         # Check if existing_user_mock should be returned based on the attribute being queried
    #         if existing_user_mock and (
    #             (target_attr == 'username' and hasattr(existing_user_mock, 'username')) or
    #             (target_attr == 'email' and hasattr(existing_user_mock, 'email'))
    #         ):
    #             print(f"--- DEBUG [validate_mock]: Returning existing_user_mock for {target_attr}")
    #             mock_chain.filter.return_value.first.return_value = existing_user_mock
    #         else:
    #             print(f"--- DEBUG [validate_mock]: Returning None for {target_attr}") 
    #             mock_chain.first.return_value = None
    #             mock_chain.filter.return_value.first.return_value = None

    #         return mock_chain # Return the mock configured for this specific filter call

    #     mock_user_query.filter.side_effect = query_side_effect

    #     errors = UserService.validate_user_data(data, user_id=user_id, is_new=is_new)
        
    #     assert errors == expected_errors, f"Test ID: {test_id}"




