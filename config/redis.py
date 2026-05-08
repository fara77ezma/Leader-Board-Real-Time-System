import os

import redis
from redis import asyncio as aioredis


REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

# Synchronous Redis client
# the connection pool reuses connections for better performance so its fine to not close it after every use
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,  # to get string responses
)

async_redis_client: aioredis.Redis | None = None


async def get_async_redis() -> aioredis.Redis:
    global async_redis_client

    if async_redis_client is None:
        async_redis_client = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
        )

    return async_redis_client


def close_sync_redis():
    redis_client.close()


async def close_async_redis():
    global async_redis_client

    if async_redis_client:
        await async_redis_client.close()
        async_redis_client = None
