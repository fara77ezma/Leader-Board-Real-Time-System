import redis
from redis import asyncio as aioredis

# Synchronous Redis client
# the connection pool reuses connections for better performance so its fine to not close it after every use
redis_client = redis.Redis(
    host="redis",  # docker service name
    port=6379,
    decode_responses=True,  # to get string responses
)

async_redis_client: aioredis.Redis | None = None


async def get_async_redis() -> aioredis.Redis:
    global async_redis_client

    if async_redis_client is None:
        async_redis_client = await aioredis.from_url(
            "redis://redis:6379",  # Using your docker service name
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
