import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from controllers.game import (
    create_new_game,
    get_games,
    deactivate_game,
    activate_game,
    delete_game,
)
from models.request import CreateGameRequest


class TestCreateNewGame:
    def test_successful_new_game_creation(self, db_session, mocker):
        """Test successfully creating a new game"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        request = CreateGameRequest(
            name="space_race",
            description="Race through space",
            is_active=True,
        )

        result = create_new_game(request=request, db=db_session)

        assert result["message"] == "New game created successfully."
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    def test_game_exists_active_returns_400(self, db_session, mocker):
        """Test creating game with existing active game name returns 400"""
        mock_game = Mock()
        mock_game.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        request = CreateGameRequest(name="space_race", is_active=True)

        with pytest.raises(HTTPException) as exc_info:
            create_new_game(request=request, db=db_session)

        assert exc_info.value.status_code == 400
        assert "Game with this name already exists" in str(exc_info.value.detail)

    def test_game_exists_inactive_reactivates(self, db_session):
        """Test reactivating inactive game"""
        mock_game = Mock()
        mock_game.is_active = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        request = CreateGameRequest(name="space_race", is_active=True)

        result = create_new_game(request=request, db=db_session)

        assert result["message"] == "Game reactivated successfully."
        assert mock_game.is_active is True
        db_session.commit.assert_called_once()

    def test_reactivation_db_failure_rolls_back(self, db_session):
        """Test reactivation handles DB failure"""
        mock_game = Mock()
        mock_game.is_active = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_game
        db_session.commit.side_effect = Exception("DB error")

        request = CreateGameRequest(name="space_race")

        with pytest.raises(HTTPException) as exc_info:
            create_new_game(request=request, db=db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to reactivate game" in str(exc_info.value.detail)
        db_session.rollback.assert_called_once()

    def test_creation_db_failure_rolls_back(self, db_session):
        """Test creation handles DB failure"""
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.commit.side_effect = Exception("DB error")

        request = CreateGameRequest(name="new_game")

        with pytest.raises(HTTPException) as exc_info:
            create_new_game(request=request, db=db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to create new game" in str(exc_info.value.detail)
        db_session.rollback.assert_called_once()


class TestGetGames:
    def test_get_all_games(self, db_session):
        """Test retrieving all games"""
        mock_game1 = Mock()
        mock_game1.name = "space_race"
        mock_game1.is_active = True

        mock_game2 = Mock()
        mock_game2.name = "chess_master"
        mock_game2.is_active = False

        db_session.query.return_value.all.return_value = [
            mock_game1,
            mock_game2,
        ]

        result = get_games(db=db_session, is_active=None)

        assert len(result) == 2
        assert result[0].name == "space_race"
        assert result[1].name == "chess_master"

    def test_get_active_games_only(self, db_session):
        """Test retrieving only active games"""
        mock_game = Mock()
        mock_game.name = "space_race"
        mock_game.is_active = True

        db_session.query.return_value.filter.return_value.all.return_value = [mock_game]

        result = get_games(db=db_session, is_active=True)

        assert len(result) == 1
        assert result[0].is_active is True

    def test_get_inactive_games_only(self, db_session):
        """Test retrieving only inactive games"""
        mock_game = Mock()
        mock_game.name = "old_game"
        mock_game.is_active = False

        db_session.query.return_value.filter.return_value.all.return_value = [mock_game]

        result = get_games(db=db_session, is_active=False)

        assert len(result) == 1
        assert result[0].is_active is False

    def test_get_empty_games_list(self, db_session):
        """Test retrieving games when none exist"""
        db_session.query.return_value.filter.return_value.all.return_value = []

        result = get_games(db=db_session, is_active=True)

        assert result == []

    def test_get_games_db_failure(self, db_session):
        """Test DB failure when retrieving games"""
        db_session.query.return_value.filter.return_value.all.side_effect = Exception(
            "DB error"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_games(db=db_session, is_active=True)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve games" in str(exc_info.value.detail)


class TestDeactivateGame:
    def test_successful_deactivation(self, db_session):
        """Test successfully deactivating an active game"""
        mock_game = Mock()
        mock_game.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        result = deactivate_game(game_name="space_race", db=db_session)

        assert result["message"] == "Game deactivated successfully."
        assert mock_game.is_active is False
        db_session.commit.assert_called_once()

    def test_deactivate_nonexistent_game(self, db_session):
        """Test deactivating non-existent game returns 404"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            deactivate_game(game_name="nonexistent", db=db_session)

        assert exc_info.value.status_code == 404
        assert "Game not found" in str(exc_info.value.detail)

    def test_deactivate_already_inactive_game(self, db_session):
        """Test deactivating already inactive game returns 400"""
        mock_game = Mock()
        mock_game.is_active = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        with pytest.raises(HTTPException) as exc_info:
            deactivate_game(game_name="space_race", db=db_session)

        assert exc_info.value.status_code == 400
        assert "Game is already deactivated" in str(exc_info.value.detail)

    def test_deactivate_db_failure_rolls_back(self, db_session):
        """Test deactivation handles DB failure"""
        mock_game = Mock()
        mock_game.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_game
        db_session.commit.side_effect = Exception("DB error")

        with pytest.raises(HTTPException) as exc_info:
            deactivate_game(game_name="space_race", db=db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to deactivate game" in str(exc_info.value.detail)
        db_session.rollback.assert_called_once()


class TestActivateGame:
    def test_successful_activation(self, db_session):
        """Test successfully activating an inactive game"""
        mock_game = Mock()
        mock_game.is_active = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        result = activate_game(game_name="space_race", db=db_session)

        assert result["message"] == "Game activated successfully."
        assert mock_game.is_active is True
        db_session.commit.assert_called_once()

    def test_activate_nonexistent_game(self, db_session):
        """Test activating non-existent game returns 404"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            activate_game(game_name="nonexistent", db=db_session)

        assert exc_info.value.status_code == 404
        assert "Game not found" in str(exc_info.value.detail)

    def test_activate_already_active_game(self, db_session):
        """Test activating already active game returns 400"""
        mock_game = Mock()
        mock_game.is_active = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        with pytest.raises(HTTPException) as exc_info:
            activate_game(game_name="space_race", db=db_session)

        assert exc_info.value.status_code == 400
        assert "Game is already active" in str(exc_info.value.detail)

    def test_activate_db_failure_rolls_back(self, db_session):
        """Test activation handles DB failure"""
        mock_game = Mock()
        mock_game.is_active = False
        db_session.query.return_value.filter.return_value.first.return_value = mock_game
        db_session.commit.side_effect = Exception("DB error")

        with pytest.raises(HTTPException) as exc_info:
            activate_game(game_name="space_race", db=db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to activate game" in str(exc_info.value.detail)
        db_session.rollback.assert_called_once()


class TestDeleteGame:
    def test_successful_deletion(self, db_session):
        """Test successfully deleting a game"""
        mock_game = Mock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_game

        result = delete_game(game_name="space_race", db=db_session)

        assert result["message"] == "Game deleted successfully."
        db_session.delete.assert_called_once_with(mock_game)
        db_session.commit.assert_called_once()

    def test_delete_nonexistent_game(self, db_session):
        """Test deleting non-existent game returns 404"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_game(game_name="nonexistent", db=db_session)

        assert exc_info.value.status_code == 404
        assert "Game not found" in str(exc_info.value.detail)

    def test_delete_db_failure_rolls_back(self, db_session):
        """Test deletion handles DB failure"""
        mock_game = Mock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_game
        db_session.commit.side_effect = Exception("DB error")

        with pytest.raises(HTTPException) as exc_info:
            delete_game(game_name="space_race", db=db_session)

        assert exc_info.value.status_code == 500
        assert "Failed to delete game" in str(exc_info.value.detail)
        db_session.rollback.assert_called_once()
