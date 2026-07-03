from fastapi import HTTPException
import pytest

from controllers.leaderboard import fetch_leaderboard, submit_score
from models.tables import Game


class TestSubmitScore:
    @pytest.mark.asyncio
    async def test_user_not_found_returns_error(
        self, db_session, make_submit_request, make_current_user
    ):
        db_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises():
            result = await submit_score(
                make_submit_request(), make_current_user(), db_session
            )
            assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_new_high_score_is_added_to_redis(
        self,
        db_session,
        mock_leaderboard_user,
        mocker,
        make_submit_request,
        make_current_user,
    ):
        existing_game = Game(name="space", is_active=True)
        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_leaderboard_user,
            existing_game,
        ]

        db_session.query.return_value.filter.return_value.all.side_effect = [
            [],
            [mock_leaderboard_user],
        ]

        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = None  # no existing score
        mock_redis.zrevrank.return_value = 0  # rank 1 (0-indexed)
        result = await submit_score(
            make_submit_request(score=150), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        assert result["score"] == 150
        assert result["rank"] == 1
        mock_redis.zadd.assert_called_once_with("leaderboard:game_001", {1: 150})

    @pytest.mark.asyncio
    async def test_lower_score_does_not_update_redis(
        self,
        db_session,
        mock_leaderboard_user,
        mocker,
        make_submit_request,
        make_current_user,
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = 200  # existing best is 200
        mock_redis.zrevrank.return_value = 2  # rank 3 (0-indexed)
        result = await submit_score(
            make_submit_request(score=100), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        assert result["score"] == 100
        assert result["rank"] == 3
        assert result["best_score"] == 200
        mock_redis.zadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_equal_score_does_not_update_redis(
        self,
        db_session,
        mock_leaderboard_user,
        mocker,
        make_submit_request,
        make_current_user,
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.return_value = 100
        mock_redis.zrevrank.return_value = 0

        result = await submit_score(
            make_submit_request(score=100), make_current_user(), db_session
        )

        assert result["message"] == "Score submitted successfully."
        mock_redis.zadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_db_commit_failure_rolls_back(
        self, db_session, mock_leaderboard_user, make_submit_request, make_current_user
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        db_session.commit.side_effect = Exception("DB error")
        with pytest.raises():
            result = await submit_score(
                make_submit_request(), make_current_user(), db_session
            )

            assert result.status_code == 500
        db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_failure_returns_error(
        self,
        db_session,
        mock_leaderboard_user,
        mocker,
        make_submit_request,
        make_current_user,
    ):
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_leaderboard_user
        )
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zscore.side_effect = Exception("Redis down")
        with pytest.raises():
            result = await submit_score(
                make_submit_request(), make_current_user(), db_session
            )
            assert result.status_code == 500


class TestFetchLeaderboard:
    def test_returns_ranked_entries(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = [("1", 200.0), ("2", 150.0)]

        # Mock first db.query(LeaderboardEntry) call
        mock_entry = mocker.Mock()
        mock_entry.user_code = "code_1"

        # Mock second db.query(User) call
        mock_user_1 = mocker.Mock()
        mock_user_1.id = 1
        mock_user_1.username = "alice"

        mock_user_2 = mocker.Mock()
        mock_user_2.id = 2
        mock_user_2.username = "bob"

        # First call returns entries, second call returns users
        db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_entry],  # first call — LeaderboardEntry
            [mock_user_1, mock_user_2],  # second call — Users
        ]

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert result["game_name"] == "game_001"
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
        mock_entry = mocker.Mock()
        mock_entry.user_code = "code_1"
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_user.username = "testuser"

        db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_entry],
            [mock_user],
        ]

        fetch_leaderboard("game_001", limit=5, db=db_session)

        mock_redis.zrevrange.assert_called_once_with(
            "leaderboard:game_001", 0, 4, withscores=True
        )

    def test_skips_entry_when_user_not_in_db(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = [("1", 200.0), ("999", 100.0)]
        mock_entry = mocker.Mock()
        mock_entry.user_code = "code_1"
        mock_user = mocker.Mock()
        mock_user.id = 1
        mock_user.username = "alice"

        # Second query returns only alice — user 999 not in DB
        db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_entry],
            [mock_user],  # only alice, no user with id 999
        ]

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert len(result["leaderboard"]) == 1
        assert result["leaderboard"][0]["username"] == "alice"

    def test_empty_leaderboard_returns_empty_list(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.return_value = []
        db_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # no leaderboard entries
            [],  # no users
        ]

        result = fetch_leaderboard("game_001", limit=10, db=db_session)

        assert result == {"game_name": "game_001", "leaderboard": []}

    def test_redis_failure_returns_error(self, db_session, mocker):
        mock_redis = mocker.patch("controllers.leaderboard.redis_client")
        mock_redis.zrevrange.side_effect = Exception("Redis down")
        db_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # no entries
            [],  # no users
        ]
        with pytest.raises(HTTPException) as exc:
            fetch_leaderboard("game_001", limit=10, db=db_session)
        assert exc.value.status_code == 500
