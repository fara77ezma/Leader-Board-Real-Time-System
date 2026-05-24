from fastapi import HTTPException,status
from sqlalchemy import func

from models.request import SubmitScoreRequest
from models.response import UserProfileResponse
from models.tables import LeaderboardEntry, User, Game
from sqlalchemy.orm import Session
from config.redis import redis_client, get_async_redis


def submit_score(
    request: SubmitScoreRequest, current_user: UserProfileResponse, db: Session
):
    # Logic to submit the score to the leaderboard
    score = request.score
    game_name = request.game_name
    user_id = current_user.id
    existing_user = db.query(User).filter(User.id == user_id).first()
    exsting_game = db.query(Game).filter(Game.name == game_name).first()
    if not existing_user or not existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if not exsting_game or not exsting_game.is_active:
       raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found."
        )

    user_code = existing_user.user_code

    # Insert in the LeaderboardEntry table (SQL)
    new_sumbission = LeaderboardEntry(
        user_code=user_code, game_name=game_name, score=score
    )
    db.add(new_sumbission)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit score.",
        )

    # Insert in Redis sorted set for quick leaderboard retrieval
    redis_key = f"leaderboard:{game_name}"
    try:
        current_best = redis_client.zscore(redis_key, user_id) or 0
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
        refresh_redis_leaderboard(game_name, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit score to Redis. Leaderboard refreshed.",
        )


def fetch_leaderboard(game_name: str, limit: int, db: Session):
    # Logic to fetch the leaderboard for a specific game
    entries = (
        db.query(LeaderboardEntry).filter(LeaderboardEntry.game_name == game_name).all()
    )
    users = (
        db.query(User)
        .filter(User.user_code.in_([entry.user_code for entry in entries]))
        .all()
    )
    user_id_username_map = {user.id: user.username for user in users}
    redis_key = f"leaderboard:{game_name}"
    try:
        top_entries = redis_client.zrevrange(
            redis_key, 0, limit - 1, withscores=True
        )  # Get top 'limit' entries in descending order with scores
        leaderboard = []
        for rank, (user_id, score) in enumerate(top_entries, start=1):
            if user_id_username_map.get(int(user_id)):
                leaderboard.append(
                    {
                        "rank": rank,
                        "username": user_id_username_map.get(int(user_id)),
                        "score": score,
                    }
                )
        return {"game_name": game_name, "leaderboard": leaderboard}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard from Redis.",
        )


def fetch_user_rank(game_name: str, current_user: UserProfileResponse) -> dict:
    user_id = current_user.id
    redis_key = f"leaderboard:{game_name}"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user rank from Redis.",
        )


async def get_player_ranks_from_redis(
    db: Session, player_id: int, player_code: str
) -> dict[str, int]:
    """
    Discover games from Redis and return player's rank in each one.
    """
    async_redis_client = await get_async_redis()

    result: dict[str, dict] = {}
    player_games = db.scalars(
        db.query(LeaderboardEntry.game_name)
        .filter(LeaderboardEntry.user_code == player_code)
        .distinct()
    ).all()

    for game_name in player_games:
        redis_key = f"leaderboard:{game_name}"
        try:
            rank = await async_redis_client.zrevrank(redis_key, player_id)
            score = await async_redis_client.zscore(redis_key, player_id)
            if rank is not None and score is not None:
                result[game_name] = {
                    "rank": rank + 1,
                    "score": score,
                }  # Convert to 1-based rank
            else:
                result[game_name] = {
                    "rank": None,
                    "score": None,
                }  # Not ranked yet
        except Exception as e:
            result[game_name] = None  # Indicate error or not ranked

    return result


def refresh_redis_leaderboard(game_name: str, db: Session):
    redis_key = f"leaderboard:{game_name}"
    redis_client.delete(redis_key)

    entries = (
        db.query(LeaderboardEntry).filter(LeaderboardEntry.game_name == game_name).all()
    )
    users = (
        db.query(User)
        .filter(User.user_code.in_([entry.user_code for entry in entries]))
        .all()
    )
    user_code_to_id = {user.user_code: user.id for user in users}
    for batch_size in range(
        0, len(entries), 500
    ):  # Batch processing to reduce Redis calls
        batch_entries = {
            user_code_to_id.get(entry.user_code): entry.score
            for entry in entries[batch_size : batch_size + 500]
        }
        redis_client.zadd(redis_key, batch_entries)

    return {"message": "Leaderboard refreshed successfully."}


def refresh_all_leaderboards(db: Session):
    game_names = db.query(LeaderboardEntry.game_name).distinct().all()
    for (game_name,) in game_names:
        refresh_redis_leaderboard(game_name, db)
    return {"message": "All leaderboards refreshed successfully."}


def refresh_user_scores_in_leaderboards(
    user_id: int, db: Session, game_name: str = None
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    user_code = user.user_code
    filter_condition = LeaderboardEntry.user_code == user_code
    if game_name:
        filter_condition = filter_condition & (LeaderboardEntry.game_name == game_name)
    best_scores = (
        db.query(
            LeaderboardEntry.game_name,
            func.max(LeaderboardEntry.score).label("best_score"),
        )
        .filter(filter_condition)
        .group_by(LeaderboardEntry.game_name)
        .all()
    )

    for entry in best_scores:
        redis_key = f"leaderboard:{entry.game_name}"
        redis_client.zadd(redis_key, {user_id: entry.best_score})

    return {"message": "User scores refreshed in leaderboards successfully."}

def fetch_around_me(game_name: str, current_user: UserProfileResponse, db: Session):
    redis_key = f"leaderboard:{game_name}"
    my_rank = redis_client.zrevrank(redis_key, current_user.id)
    last_rank = redis_client.zcard(redis_key) - 1 
    
    if my_rank is None:
        return {"message": "User not ranked yet."}
    
    start = max(0, my_rank - 2)  
    shortage = 2 - (my_rank - start)
    end = my_rank + 2 + shortage
    
    if end > last_rank:
        end = last_rank
        start = max(0, end - 4)
    
    try: 
        entries = redis_client.zrevrange(redis_key,start,end,withscores=True)
        
        users = (
            db.query(User)
            .filter(User.id.in_([int(user_id) for user_id, _ in entries]))
            .all()
        )
        user_name_id_map = {user.id: user.username for user in users}
        return {
            "game_name": game_name,
            "leaderboard": [
                {
                    "rank": start + rank + 1,
                    "username": user_name_id_map.get(int(user_id), "Unknown"),
                    "score": score,
                    "is_me": int(user_id) == current_user.id,
                }
                for rank, (user_id, score) in enumerate(entries)
            ],
        }
    except Exception as e:
        raise HTTPException(  
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch around me leaderboard.",
                )
 