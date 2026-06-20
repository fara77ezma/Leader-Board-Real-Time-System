import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from controllers.users import (
    deactivate_user_account,
    reactivate_account,
    delete_user_account,
)
from models.response import UserProfileResponse


class TestDeactivateUserAccount:
    @pytest.mark.asyncio
    async def test_successful_deactivation(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mock_redis = Mock()
        mock_redis.keys.return_value = []
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        result = await deactivate_user_account(db_session, current_user)

        assert result["message"] == "account deactivated successfully."
        assert mock_user.is_active is False
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivation_revokes_refresh_tokens(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        db_session.query.return_value.filter.return_value.update = Mock(return_value=2)

        mock_redis = Mock()
        mock_redis.keys.return_value = []
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        await deactivate_user_account(db_session, current_user)

        # Verify update was called (revoke tokens)
        db_session.query.return_value.filter.return_value.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivation_cleans_redis_leaderboards(self, db_session, mocker):
        """Test deactivation removes user from Redis leaderboards"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mock_redis = Mock()
        mock_redis.keys.return_value = [
            "leaderboard:game1",
            "leaderboard:game2",
            "leaderboard:game3",
        ]
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        await deactivate_user_account(db_session, current_user)

        # Verify zrem called for each leaderboard
        assert mock_redis.zrem.call_count >= 3
        mock_redis.keys.assert_called_once_with("leaderboard:*")

    @pytest.mark.asyncio
    async def test_deactivation_db_error_rolls_back(self, db_session, mocker):
        """Test deactivation handles database errors"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit.side_effect = Exception("DB error")

        mock_redis = Mock()
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        with pytest.raises(HTTPException) as exc_info:
            await deactivate_user_account(db_session, current_user)

        assert exc_info.value.status_code == 500
        db_session.rollback.assert_called_once()


class TestReactivateAccount:
    def test_successful_reactivation(self, db_session, mocker):
        """Test successfully reactivating deactivated account"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False
        mock_user.is_verified = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mocker.patch("controllers.users.auth.verify_password", return_value=True)
        mocker.patch("controllers.users.auth.generate_token", return_value="test_token")
        mocker.patch(
            "controllers.users.auth.generate_refresh_token",
            return_value="refresh_token",
        )

        result = reactivate_account(
            email="test@example.com", password="TestPass123", db=db_session
        )

        assert result["message"] == "Account reactivated successfully."
        assert result["token"] == "test_token"
        assert result["refresh_token"] == "refresh_token"
        assert mock_user.is_active is True
        db_session.commit.assert_called_once()

    def test_reactivation_user_not_found(self, db_session):
        """Test reactivation with non-existent user returns 404"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            reactivate_account(
                email="nonexistent@example.com", password="TestPass123", db=db_session
            )

        assert exc_info.value.status_code == 404

    def test_reactivation_already_active(self, db_session):
        """Test reactivating already active account returns success"""
        mock_user = Mock()
        mock_user.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = reactivate_account(
            email="test@example.com", password="TestPass123", db=db_session
        )

        assert result["message"] == "Account is already active."

    def test_reactivation_wrong_password(self, db_session, mocker):
        """Test reactivation with wrong password returns 403"""
        mock_user = Mock()
        mock_user.is_active = False
        mock_user.is_verified = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mocker.patch("controllers.users.auth.verify_password", return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            reactivate_account(
                email="test@example.com", password="WrongPassword", db=db_session
            )

        assert exc_info.value.status_code == 403
        assert "Invalid password" in str(exc_info.value.detail)

    def test_reactivation_unverified_email(self, db_session, mocker):
        """Test reactivation with unverified email returns 403"""
        mock_user = Mock()
        mock_user.is_active = False
        mock_user.is_verified = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mocker.patch("controllers.users.auth.verify_password", return_value=True)

        with pytest.raises(HTTPException) as exc_info:
            reactivate_account(
                email="test@example.com", password="TestPass123", db=db_session
            )

        assert exc_info.value.status_code == 403
        assert "Email not verified" in str(exc_info.value.detail)

    def test_reactivation_db_error(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False
        mock_user.is_verified = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit.side_effect = Exception("DB error")

        mocker.patch("controllers.users.auth.verify_password", return_value=True)
        mocker.patch("controllers.users.auth.generate_token", return_value="test_token")
        mocker.patch(
            "controllers.users.auth.generate_refresh_token",
            return_value="refresh_token",
        )

        with pytest.raises(HTTPException) as exc_info:
            reactivate_account(
                email="test@example.com", password="TestPass123", db=db_session
            )

        assert exc_info.value.status_code == 500
        db_session.rollback.assert_called_once()


class TestDeleteUserAccount:
    @pytest.mark.asyncio
    async def test_successful_deletion(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mock_redis = Mock()
        mock_redis.keys.return_value = []
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        result = await delete_user_account(db_session, current_user)

        assert result["message"] == "account deleted successfully."
        db_session.delete.assert_called_once_with(mock_user)
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deletion_cleans_redis_leaderboards(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        mock_redis = Mock()
        mock_redis.keys.return_value = ["leaderboard:game1", "leaderboard:game2"]
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        await delete_user_account(db_session, current_user)

        # Verify zrem called for each leaderboard
        assert mock_redis.zrem.call_count >= 2

    @pytest.mark.asyncio
    async def test_deletion_db_error_rolls_back(self, db_session, mocker):
        mock_user = Mock()
        mock_user.id = 1
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit.side_effect = Exception("DB error")

        mock_redis = Mock()
        mocker.patch("controllers.users.redis_client", mock_redis)

        current_user = UserProfileResponse(
            id=1,
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            games={},
            is_verified=True,
            created_at="2024-01-01",
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_user_account(db_session, current_user)

        assert exc_info.value.status_code == 500
        db_session.rollback.assert_called_once()
