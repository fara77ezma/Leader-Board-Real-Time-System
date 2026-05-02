import pytest
from types import SimpleNamespace
from controllers.leaderboard import fetch_leaderboard, submit_score
from models.request import SubmitScoreRequest


def make_submit_request(game_id="game_001", score=100):
    return SubmitScoreRequest(game_id=game_id, score=score)


def make_current_user(user_id=1, username="testuser"):
    return SimpleNamespace(id=user_id, username=username)


@pytest.fixture
def mock_leaderboard_user(mocker):
    user = mocker.Mock()
    user.id = 1
    user.username = "testuser"
    user.user_code = "test-uuid-123"
    return user


class TestSubmitScore:
    def test_user_not_found_returns_error(self, db_session):
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = submit_score(make_submit_request(), make_current_user(), db_session)

        assert result == {"error": "User not found."}

    def test_new_high_score_is_added_to_redis(
        self, db_session, mock_leaderboard_user, mocker
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = None  # no existing score
        mock_redis.zrevrank.return_value = 0  # rank 1 (0-indexed)

        result = submit_score(
            make_submit_request(score=150), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        assert result["score"] == 150
        assert result["rank"] == 1
        mock_redis.zadd.assert_called_once_with("leaderboard:game_001", {1: 150})

    def test_lower_score_does_not_update_redis(
        self, db_session, mock_leaderboard_user, mocker
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = 200  # existing best is 200
        mock_redis.zrevrank.return_value = 2  # rank 3 (0-indexed)

        result = submit_score(
            make_submit_request(score=100), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        assert result["score"] == 100
        assert result["rank"] == 3
        mock_redis.zadd.assert_not_called()

    def test_equal_score_does_not_update_redis(
        self, db_session, mock_leaderboard_user, mocker
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = 100
        mock_redis.zrevrank.return_value = 0

        result = submit_score(
            make_submit_request(score=100), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        mock_redis.zadd.assert_not_called()

    def test_db_commit_failure_rolls_back(self, db_session, mock_leaderboard_user):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        db_session.commit.side_effect = Exception("DB error")

        result = submit_score(make_submit_request(), make_current_user(), db_session)

        assert result == {"error": "Score submission failed."}
        db_session.rollback.assert_called_once()

    def test_redis_failure_returns_error(
        self, db_session, mock_leaderboard_user, mocker
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.side_effect = Exception("Redis down")
        breakpoint()

        result = submit_score(make_submit_request(), make_current_user(), db_session)
        assert result == {"error": "Score submission failed at leaderboard update."}


class TestFetchLeaderboard:
    def test_returns_ranked_entries(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = [("1", 200.0), ("2", 150.0)]

        alice = mocker.Mock()
        alice.username = "alice"
        bob = mocker.Mock()
        bob.username = "bob"
        db_session.query.return_value.filter.return_value.first.side_effect = [
            alice,
            bob,
        ]

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert result["game_id"] == "game_001"
        assert len(result["leaderboard"]) == 2
        assert result["leaderboard"][0] == {
            "rank": 1,
            "username": "alice",
            "score": 200.0,
        }
        assert result["leaderboard"][1] == {
            "rank": 2,
            "username": "bob",
            "score": 150.0,
        }

    def test_respects_limit_parameter(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = [("1", 500.0)]
        user = mocker.Mock()
        user.username = "testuser"
        db_session.query.return_value.filter.return_value.first.return_value = user

        fetch_leaderboard("game_001", limit=5, db=db_session)

        mock_redis.zrevrange.assert_called_once_with(
            "leaderboard:game_001", 0, 4, withscores=True
        )

    def test_skips_entry_when_user_not_in_db(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = [("1", 200.0), ("999", 100.0)]

        alice = mocker.Mock()
        alice.username = "alice"
        db_session.query.return_value.filter.return_value.first.side_effect = [
            alice,
            None,
        ]

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert len(result["leaderboard"]) == 1
        assert result["leaderboard"][0]["username"] == "alice"

    def test_empty_leaderboard_returns_empty_list(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = []

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert result == {"game_id": "game_001", "leaderboard": []}

    def test_redis_failure_returns_error(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.side_effect = Exception("Redis down")

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert result == {"error": "Failed to fetch leaderboard."}
