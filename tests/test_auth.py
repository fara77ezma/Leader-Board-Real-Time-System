import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from controllers.auth import (
    delete_expired_refresh_tokens,
    email_verification,
    generate_refresh_token,
    hash_password,
    login_user,
    refresh_access_token,
    revoke_refresh_token,
    verify_password,
    generate_token,
    SECRET_KEY,
    ALGORITHM,
    verify_token,
)
from datetime import datetime, timedelta, timezone
import jwt


class TestPasswordHashing:
    def test_hash_password_creates_hash(self):
        password = "MySecretPassword"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_hash_password_different_for_different_passwords(self):
        password1 = "PasswordOne"
        password2 = "PasswordTwo"
        hashed1 = hash_password(password1)
        hashed2 = hash_password(password2)
        assert hashed1 != hashed2

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
        verified_hash = verify_password(password, hashed)
        assert verified_hash == True

    def test_verify_incorrect_password(self):
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = hash_password(password)
        assert hashed is not None
        verified_hash = verify_password(wrong_password, hashed)
        assert verified_hash == False


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_successful_registration(
        self, db_session, sample_register_request, mocker
    ):
        db_session.query.return_value.filter.return_value.first.return_value = None
        mocker.patch("controllers.auth.send_auth_email", return_value=True)

        from controllers.auth import register_user

        result = await register_user(sample_register_request, db_session)

        assert result.requires_verification is True
        assert "Registration successful" in result.message
        db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_user_raises_conflict(
        self, db_session, sample_register_request, mock_user
    ):
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        from controllers.auth import register_user

        with pytest.raises(HTTPException) as exc_info:
            await register_user(sample_register_request, db_session)

        assert exc_info.value.status_code == 409
        db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_commit_failure_raises_500(
        self, db_session, sample_register_request
    ):
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.commit.side_effect = Exception("DB error")

        from controllers.auth import register_user

        with pytest.raises(HTTPException) as exc_info:
            await register_user(sample_register_request, db_session)

        assert exc_info.value.status_code == 500
        db_session.rollback.assert_called_once()


class TestLogin:
    def test_successful_login(
        self, mocker, db_session, sample_login_request, mock_user
    ):
        # Mock the database query to return the mock user
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mocker.patch("controllers.auth.verify_password", return_value=True)
        # Call the login_user function
        response = login_user(sample_login_request, db_session)

        # Assertions
        assert "token" in response
        assert response["message"] == "Login successful."


class TestGenerateToken:
    def test_generate_token_creates_valid_jwt(self):
        token = generate_token(user_id=1, username="testuser")

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_generate_token_payload_structure(self):

        token = generate_token(user_id=42, username="alice")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert payload["user_id"] == 42
        assert payload["username"] == "alice"
        assert "exp" in payload

    def test_generate_token_expiry_set(self):

        token = generate_token(user_id=1, username="testuser")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Token should expire in ~1 hour (within 1 minute tolerance)
        time_diff = (exp_time - now).total_seconds()
        assert 3540 <= time_diff <= 3660  # Between 59-61 minutes


class TestVerifyToken:
    def test_verify_token_valid_token(self):
        token = generate_token(user_id=1, username="testuser")
        payload = verify_token(token)

        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"

    def test_verify_token_expired_token(self, mocker):
        # Create expired token (expired 1 hour ago)
        expired_payload = {
            "user_id": 1,
            "username": "testuser",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)

        assert exc_info.value.status_code == 401

    def test_verify_token_invalid_token(self):

        invalid_token = "invalid.token.string"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401


class TestGenerateRefreshToken:
    def test_generate_refresh_token_creates_record(self, db_session, mocker):
        token = generate_refresh_token(user_id=1, db=db_session)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    def test_generate_refresh_token_returns_string(self, db_session):
        token = generate_refresh_token(user_id=1, db=db_session)

        assert isinstance(token, str)
        assert len(token) > 0


class TestRevokeRefreshToken:
    def test_revoke_refresh_token_sets_flag(self, db_session):
        mock_token = Mock()
        mock_token.is_revoked = False
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_token
        )

        result = revoke_refresh_token(db=db_session, refresh_token="test_token")

        assert result["message"] == "Logged out successfully."
        assert mock_token.is_revoked is True
        db_session.commit.assert_called_once()

    def test_revoke_refresh_token_not_found(self, db_session):
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            revoke_refresh_token(db=db_session, refresh_token="invalid_token")

        assert exc_info.value.status_code == 401


class TestRefreshAccessToken:
    def test_refresh_access_token_generates_new_token(self, db_session, mocker):
        mock_refresh_record = Mock()
        mock_refresh_record.user_id = 1
        mock_refresh_record.is_revoked = False
        mock_refresh_record.expires_at = datetime.now(timezone.utc) + timedelta(days=1)

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"

        db_session.query.filter.return_value.first.side_effect = [
            mock_refresh_record,
            mock_user,
        ]

        mocker.patch("controllers.auth.generate_token", return_value="new_token")

        result = refresh_access_token("valid_token", db_session)

        assert result["token"] == "new_token"


class TestEmailVerification:
    def test_email_verification_success(self, db_session):
        mock_user = Mock()
        mock_user.is_verified = False
        mock_user.email_verification_code = "valid_code"
        mock_user.email_verification_expiry = datetime.now(timezone.utc) + timedelta(
            hours=1
        )

        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = email_verification("valid_code", db_session)

        assert result["message"] == "Email verified successfully."
        assert mock_user.is_verified is True
        assert mock_user.email_verification_code is None
        db_session.commit.assert_called_once()

    def test_email_verification_invalid_code(self, db_session):

        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            email_verification("invalid_code", db_session)

        assert exc_info.value.status_code == 400

    def test_email_verification_expired_code(self, db_session):
        mock_user = Mock()
        mock_user.is_verified = False
        mock_user.email_verification_expiry = datetime.now(timezone.utc) - timedelta(
            hours=1
        )  # Expired

        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException):
            result = email_verification("expired_code", db_session)
            assert result.json()["detail"] == "Verification code has expired."
            assert result.status_code == 500


class TestDeleteExpiredRefreshTokens:
    def test_delete_expired_refresh_tokens(self, db_session):
        mock_filter = Mock()
        db_session.query.return_value.filter.return_value = mock_filter

        delete_expired_refresh_tokens(db_session)

        mock_filter.delete.assert_called_once()
        db_session.commit.assert_called_once()

    def test_delete_expired_refresh_tokens_db_error(self, db_session):

        db_session.query.return_value.filter.return_value.delete.return_value = None

        db_session.commit.side_effect = Exception("DB error")

        with pytest.raises(HTTPException) as exc_info:
            delete_expired_refresh_tokens(db_session)
        #
        assert exc_info.value.status_code == 500
