from controllers.auth import hash_password, login_user, verify_password
from fixtures.auth_fixtures import mock_db, sample_login_request, mock_user
from models.request import LoginRequest


class TestPasswordHashing:
    def test_hash_password_creates_hash(self):
        password = "MySecretPassword"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    def test_hash_password_is_consistent(self):
        password = "AnotherPassword"
        hashed1 = hash_password(password)
        hashed2 = hash_password(password)
        assert hashed1 == hashed2
    def test_hash_password_different_for_different_passwords(self):
        password1 = "PasswordOne"
        password2 = "PasswordTwo"
        hashed1 = hash_password(password1)
        hashed2 = hash_password(password2)
        assert hashed1 != hashed2
    
    def test_hash_password_handles_empty_string(self):
        password = ""
        hashed = hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    def test_hash_password_handles_special_characters(self):
        password = "P@$$w0rd!#%"
        hashed = hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    def test_verfy_hashed_password(self):
        password = "VerifyMe123"
        hashed = hash_password(password)
        assert hashed is not None
        assert hashed != password
        # Verify by hashing again and comparing
        verified_hash = verify_password(password,hashed)
        assert verified_hash == True
    def test_verify_incorrect_password(self):
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = hash_password(password)
        assert hashed is not None
        verified_hash = verify_password(wrong_password,hashed)
        assert verified_hash == False
    def test_verify_empty_password(self):
        password = ""
        hashed = hash_password(password)
        assert hashed is not None
        verified_hash = verify_password(password,hashed)
        assert verified_hash == True
    
class TestLogin:
    def test_successful_login(self, mocker, db_session):
        # Mock the database query to return the mock user
        mocker.patch.object(db_session, 'query', return_value=mocker.MagicMock(
            filter=mocker.MagicMock(
                first=mocker.MagicMock(return_value=mock_user())
            )
        ))
        # Create a login request
        login_request = sample_login_request()
        # Call the login_user function
        response = login_user(login_request, db_session)
        # Assertions
        assert "token" in response
        assert response["message"] == "Login successful."
        