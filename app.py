from fastapi import FastAPI
from models.tables import Base
from routes import auth, users, leaderboard, game
from controllers.auth import delete_expired_refresh_tokens
from config.db import engine, get_db
from config.redis import close_sync_redis, close_async_redis, get_async_redis, redis_client, async_redis_client
from fastapi.security import HTTPBearer
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi_limiter import FastAPILimiter

app = FastAPI()

security = HTTPBearer()
scheduler = AsyncIOScheduler()

@app.get("/health")
def health_check():
    try:
        engine.connect()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {e}"
    
    try:
        redis_client.ping()
        redis_sync_status = "healthy"
    except Exception as e:
        redis_sync_status = f"unhealthy: {e}"
    
    try:
        async_redis_client.ping()
        redis_async_status = "healthy"
    except Exception as e:
        redis_async_status = f"unhealthy: {e}"
        
    return {
        "status": "healthy" if db_status == "healthy" and redis_async_status == "healthy"  and redis_sync_status == "healthy" else "unhealthy",
        "database": db_status,
        "redis_sync": redis_sync_status,
        "redis_async": redis_async_status,
    }

    

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    try:
        redis = await get_async_redis()
        await FastAPILimiter.init(redis)
        print("FastAPILimiter initialized successfully.")
    except Exception as e:
        print(f"Error initializing FastAPILimiter: {e}")
        
    scheduler.add_job(
        cleanup_job, 
        trigger="interval", # run the job at regular intervals
        hours = 24, # run every 24 hours
        id="cleanup_expired_tokens",
    )
    scheduler.start()


@app.get("/")
def root():
    return {"message": "Hi By Farah"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaderboard.router)
app.include_router(game.router)


@app.on_event("shutdown")
async def shutdown():
    close_sync_redis()
    await close_async_redis()
    print("Redis connections closed.")
    scheduler.shutdown()

def cleanup_job():
    db = next(get_db())  # get a db session
    try:
        delete_expired_refresh_tokens(db)
        print("Expired tokens cleaned up successfully.")
    except Exception as e:
        print(f"Error cleaning up expired tokens: {e}")
    finally:
        db.close()  # always close the session