from sqlalchemy import func

from models.request import SubmitScoreRequest
from models.response import UserProfileResponse
from models.tables import LeaderboardEntry, User
from sqlalchemy.orm import Session
from config.redis import redis_client, get_async_redis


def submit_score(
    request: SubmitScoreRequest, current_user: UserProfileResponse, db: Session
):
    # Logic to submit the score to the leaderboard
    score = request.score
    game_id = request.game_id
    user_id = current_user.id
    existing_user = db.query(User).filter(User.id == current_user.id).first()
    if not existing_user or not existing_user.is_active:
        return {"error": "User not found."}
    user_code = existing_user.user_code

    # Insert in the LeaderboardEntry table (SQL)
    new_sumbission = LeaderboardEntry(user_code=user_code, game_id=game_id, score=score)
    db.add(new_sumbission)
    try:
        db.commit()
    except Exception as e:
        print("Error during score submission:", e)
        db.rollback()
        return {"error": "Score submission failed."}

    # Insert in Redis sorted set for quick leaderboard retrieval
    redis_key = f"leaderboard:{game_id}"
    try:
        current_best = redis_client.zscore(redis_key, user_id) or 0
        print("Current best score in Redis:", current_best)

        if score <= current_best:
            rank = redis_client.zrevrank(redis_key, user_id)
            return {
                "message": "Score submitted successfully.",
                "best_score": current_best,
                "score": score,
                "rank": rank + 1,
            }
        else:

            redis_client.zadd(redis_key, {user_id: score})
            rank = redis_client.zrevrank(redis_key, user_id)
            return {
                "message": "Score submitted successfully.",
                "previous_best": current_best,
                "score": score,
                "rank": rank + 1,
            }  # rank is 0-based
    except Exception as e:
        print("Error updating Redis leaderboard:", e)
        refresh_redis_leaderboard(game_id, db)
        return {"error": "Score submission failed at leaderboard update."}


def fetch_leaderboard(game_id: str, limit: int, db: Session):
    # Logic to fetch the leaderboard for a specific game
    entries = (
        db.query(LeaderboardEntry).filter(LeaderboardEntry.game_id == game_id).all()
    )
    users = (
        db.query(User)
        .filter(User.user_code.in_([entry.user_code for entry in entries]))
        .all()
    )
    user_id_username_map = {user.id: user.username for user in users}
    redis_key = f"leaderboard:{game_id}"
    try:
        top_entries = redis_client.zrevrange(
            redis_key, 0, limit - 1, withscores=True
        )  # Get top 'limit' entries in descending order with scores
        print("Top entries from Redis:", top_entries)
        leaderboard = []
        for rank, (user_id, score) in enumerate(top_entries, start=1):
            if user_id_username_map.get(user_id):
                leaderboard.append(
                    {
                        "rank": rank,
                        "username": user_id_username_map.get(user_id),
                        "score": score,
                    }
                )
        return {"game_id": game_id, "leaderboard": leaderboard}
    except Exception as e:
        print("Error fetching leaderboard from Redis:", e)
        return {"error": "Failed to fetch leaderboard."}


def fetch_user_rank(game_id: str, current_user: UserProfileResponse) -> dict:
    user_id = current_user.id
    redis_key = f"leaderboard:{game_id}"
    try:
        rank = redis_client.zrevrank(redis_key, user_id)
        if rank is None:
            return {"message": "User not ranked yet."}
        else:
            score = redis_client.zscore(redis_key, user_id)
            return {
                "user_id": user_id,
                "rank": rank + 1,
                "score": score,
            }  # rank is 0-based
    except Exception as e:
        print("Error fetching user rank from Redis:", e)
        return {"error": "Failed to fetch user rank."}


async def get_player_ranks_from_redis(player_id: int) -> dict[str, int]:
    """
    Discover games from Redis and return player's rank in each one.
    """
    async_redis_client = await get_async_redis()

    result: dict[str, int] = {}
    cursor = 0

    while True:
        cursor, keys = await async_redis_client.scan(
            cursor=cursor, match="leaderboard:*", count=100
        )

        for key in keys:
            rank = await async_redis_client.zrevrank(key, str(player_id))

            if rank is not None:
                game_id = key[len("leaderboard:") :]
                current_score = (
                    await async_redis_client.zscore(key, str(player_id)) or 0
                )
                result[game_id] = {"score": current_score, "rank": rank + 1}

        if cursor == 0:
            break

    return result


def refresh_redis_leaderboard(game_id: str, db: Session):
    redis_key = f"leaderboard:{game_id}"
    redis_client.delete(redis_key)

    entries = (
        db.query(LeaderboardEntry).filter(LeaderboardEntry.game_id == game_id).all()
    )
    users = (
        db.query(User)
        .filter(User.user_code.in_([entry.user_code for entry in entries]))
        .all()
    )
    user_code_to_id = {user.user_code: user.id for user in users}
    for entry in range(0, len(entries), 500):  # Batch processing to reduce Redis calls
        batch_entries = {
            user_code_to_id.get(entry.user_code): entry.score
            for entry in entries[entry : entry + 500]
        }
        redis_client.zadd(redis_key, batch_entries)

    return {"message": "Leaderboard refreshed successfully."}


def refresh_all_leaderboards(db: Session):
    game_ids = db.query(LeaderboardEntry.game_id).distinct().all()
    for (game_id,) in game_ids:
        refresh_redis_leaderboard(game_id, db)
    return {"message": "All leaderboards refreshed successfully."}


def refresh_user_scores_in_leaderboards(user_id: int, db: Session, game_id: str = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found."}

    user_code = user.user_code
    filter_condition = LeaderboardEntry.user_code == user_code
    if game_id:
        filter_condition = filter_condition & (LeaderboardEntry.game_id == game_id)
    best_scores = (
        db.query(
            LeaderboardEntry.game_id,
            func.max(LeaderboardEntry.score).label("best_score"),
        )
        .filter(filter_condition)
        .group_by(LeaderboardEntry.game_id)
        .all()
    )

    for entry in best_scores:
        redis_key = f"leaderboard:{entry.game_id}"
        redis_client.zadd(redis_key, {user_id: entry.best_score})

    return {"message": "User scores refreshed in leaderboards successfully."}
