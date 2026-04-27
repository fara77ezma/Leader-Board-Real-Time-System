from unittest.mock import Mock
from models.request import SubmitScoreRequest
from models.tables import User


def make_submit_request(game_id="game_001", score=100):
    return SubmitScoreRequest(game_id=game_id, score=score)


def mock_leaderboard_user(user_id=1, username="testuser", user_code="test-uuid-123"):
    user = Mock(spec=User)
    user.id = user_id
    user.username = username
    user.user_code = user_code
    return user


def current_user(user_id=1, username="testuser"):
    return {"user_id": user_id, "username": username}
