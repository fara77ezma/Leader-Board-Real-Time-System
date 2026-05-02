import pytest
from fastapi import HTTPException
from unittest.mock import Mock
from controllers.users import (
    get_current_user,
    get_user_profile,
    update_user_profile,
    remove_user_avatar,
)


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, mocker, db_session, mock_user_from_db
    ):
        """Test successfully retrieving current user's profile"""
        # Mock token verification (patch where it's imported from)
        mocker.patch(
            "controllers.auth.verify_token",
            return_value={"user_id": 1, "username": "testuser"},
        )

        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_user_from_db
        )

        # Mock Redis player ranks
        mocker.patch(
            "controllers.users.get_player_ranks_from_redis",
            return_value={"game_001": {"score": 100, "rank": 1}},
        )

        result = await get_current_user(
            db=db_session, token=Mock(credentials="valid_token")
        )

        assert result.id == 1
        assert result.username == "testuser"
        assert result.avatar_url == "https://example.com/avatar.jpg"
        assert result.is_verified is True

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mocker, db_session):
        """Test with invalid token"""
        mocker.patch(
            "controllers.auth.verify_token",
            return_value={"error": "Invalid token"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                db=db_session, token=Mock(credentials="invalid_token")
            )

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mocker, db_session):
        """Test when user doesn't exist in database"""
        mocker.patch(
            "controllers.auth.verify_token",
            return_value={"user_id": 999, "username": "nonexistent"},
        )
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db=db_session, token=Mock(credentials="valid_token"))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, mocker, db_session):
        """Test when user is inactive"""
        inactive_user = Mock()
        inactive_user.id = 1
        inactive_user.is_active = False

        mocker.patch(
            "controllers.auth.verify_token",
            return_value={"user_id": 1, "username": "testuser"},
        )
        db_session.query.return_value.filter.return_value.first.return_value = (
            inactive_user
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(db=db_session, token=Mock(credentials="valid_token"))

        assert exc_info.value.status_code == 404


class TestGetUserProfile:
    @pytest.mark.asyncio
    async def test_get_user_profile_success(
        self, mocker, db_session, mock_different_user
    ):
        """Test successfully retrieving another user's profile"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_different_user
        )

        mocker.patch(
            "controllers.users.get_player_ranks_from_redis",
            return_value={"game_002": {"score": 250, "rank": 2}},
        )

        result = await get_user_profile("otheruser", db=db_session)

        assert result.username == "otheruser"
        assert result.avatar_url == "https://example.com/other.jpg"
        assert "game_002" in result.games

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, mocker, db_session):
        """Test when profile doesn't exist"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_user_profile("nonexistent", db=db_session)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_user_profile_no_games(
        self, mocker, db_session, mock_different_user
    ):
        """Test user profile with no game history"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_different_user
        )

        mocker.patch(
            "controllers.users.get_player_ranks_from_redis",
            return_value={},
        )

        result = await get_user_profile("otheruser", db=db_session)

        assert result.username == "otheruser"
        assert result.games == {}


class TestUpdateUserProfile:
    @pytest.mark.asyncio
    async def test_update_avatar_success(
        self, mocker, db_session, mock_current_user, mock_upload_file
    ):
        """Test successfully updating user avatar"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock Cloudinary upload
        mocker.patch(
            "controllers.users.upload_avatar",
            return_value="https://cloudinary.com/new_avatar.jpg",
        )

        result = await update_user_profile(
            db_session, mock_current_user, mock_upload_file
        )

        assert result["message"] == "avatar updated successfully."
        assert mock_user.avatar_url == "https://cloudinary.com/new_avatar.jpg"
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_avatar_user_not_found(
        self, mocker, db_session, mock_current_user, mock_upload_file
    ):
        """Test updating avatar when user doesn't exist"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await update_user_profile(db_session, mock_current_user, mock_upload_file)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_avatar_db_error(
        self, mocker, db_session, mock_current_user, mock_upload_file
    ):
        """Test avatar update with database error"""
        mock_user = Mock()
        mock_user.id = 1
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit.side_effect = Exception("DB error")

        mocker.patch(
            "controllers.users.upload_avatar",
            return_value="https://cloudinary.com/new_avatar.jpg",
        )

        with pytest.raises(Exception):
            result = await update_user_profile(
                db_session, mock_current_user, mock_upload_file
            )
            assert result.status_code == 500
            assert "Failed to update user profile" in str(result.detail)


class TestRemoveUserAvatar:
    @pytest.mark.asyncio
    async def test_remove_avatar_success(self, mocker, db_session, mock_current_user):
        """Test successfully removing user avatar"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock Cloudinary delete
        mocker.patch("controllers.users.delete_avatar", return_value=None)

        # Mock default avatar generation
        generate_mock = mocker.patch(
            "controllers.users.generate_default_avatar",
            return_value="https://ui-avatars.com/api/?name=testuser&size=200&background=random&color=fff&bold=true",
        )

        result = await remove_user_avatar(db_session, mock_current_user)

        assert result["message"] == "avatar deleted successfully."
        generate_mock.assert_called_once_with(username="testuser")
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_remove_avatar_user_not_found(
        self, mocker, db_session, mock_current_user
    ):
        """Test removing avatar when user doesn't exist"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await remove_user_avatar(db_session, mock_current_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_avatar_db_error(self, mocker, db_session, mock_current_user):
        """Test avatar removal with database error"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit.side_effect = Exception("DB error")

        mocker.patch("controllers.users.delete_avatar", return_value=None)
        mocker.patch(
            "controllers.users.generate_default_avatar",
            return_value="https://ui-avatars.com/api/?name=testuser",
        )

        with pytest.raises(Exception):
            result = await remove_user_avatar(db_session, mock_current_user)
            assert result.status_code == 500
            assert "Failed to delete user avatar" in str(result.detail)

    @pytest.mark.asyncio
    async def test_remove_avatar_cloudinary_error(
        self, mocker, db_session, mock_current_user
    ):
        """Test avatar removal with Cloudinary error"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock Cloudinary delete with error
        mocker.patch(
            "controllers.users.delete_avatar",
            side_effect=Exception("Cloudinary error"),
        )

        with pytest.raises(Exception):
            result = await remove_user_avatar(db_session, mock_current_user)
            assert result.status_code == 500
            assert "Failed to delete user avatar" in str(result.detail)
