from datetime import datetime
from time import time
from db import db
from models.request import SubmitScoreRequest
from models.tables import LeaderboardEntry, User
from sqlalchemy.orm import Session
import redis

redis_client = redis.Redis(
    host="redis",  # docker service name
    port=6379,
    decode_responses=True,  # to get string responses
)


def submit_score(request: SubmitScoreRequest, current_user: dict, db: Session):
    # Logic to submit the score to the leaderboard
    score = request.score
    game_id = request.game_id
    user_id = current_user["user_id"]
    existing_user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not existing_user:
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
    current_best = redis_client.zscore(redis_key, user_id) or 0
    try:
        print("Current best score in Redis:", current_best)

        if score <= current_best:
            return {
                "message": "Score submitted successfully.",
                "best_score": current_best,
                "score": score,
                "rank": redis_client.zrevrank(redis_key, user_id) + 1,
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
        return {"error": "Score submission failed at leaderboard update."}


def fetch_leaderboard(game_id: str, limit: int, db: Session):
    # Logic to fetch the leaderboard for a specific game
    redis_key = f"leaderboard:{game_id}"
    try:
        top_entries = redis_client.zrevrange(
            redis_key, 0, limit - 1, withscores=True
        )  # Get top 'limit' entries in descending order with scores
        print("Top entries from Redis:", top_entries)
        leaderboard = []
        for rank, (user_id, score) in enumerate(top_entries, start=1):
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:
                leaderboard.append(
                    {"rank": rank, "username": user.username, "score": score}
                )
        return {"game_id": game_id, "leaderboard": leaderboard}
    except Exception as e:
        print("Error fetching leaderboard from Redis:", e)
        return {"error": "Failed to fetch leaderboard."}


def fetch_user_rank(game_id: str, current_user: dict, db: Session):
    user_id = current_user["user_id"]
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
