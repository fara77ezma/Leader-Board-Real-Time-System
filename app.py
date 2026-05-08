from fastapi import FastAPI
from models.tables import Base
from routes import auth, users, leaderboard
from config.db import engine
from config.redis import close_sync_redis, close_async_redis, get_async_redis
from fastapi.security import HTTPBearer

from fastapi_limiter import FastAPILimiter


app = FastAPI()

security = HTTPBearer()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    try:
        redis = await get_async_redis()
        await FastAPILimiter.init(redis)
        print("FastAPILimiter initialized successfully.")
    except Exception as e:
        print(f"Error initializing FastAPILimiter: {e}")


@app.get("/")
def root():
    return {"message": "Hi By Farah"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaderboard.router)


@app.on_event("shutdown")
async def shutdown():
    close_sync_redis()
    await close_async_redis()
    print("Redis connections closed.")
