import uuid

INSTANCE_ID = str(uuid.uuid4())


async def acquire_leader(redis, channel, key, ttl=10):
    lock_key = f"leader:{channel}:{key}"
    return await redis.set(lock_key, INSTANCE_ID, nx=True, ex=ttl)


async def refresh_leader(redis, channel, key, ttl=10):
    lock_key = f"leader:{channel}:{key}"
    current = await redis.get(lock_key)
    if current == INSTANCE_ID:
        await redis.expire(lock_key, ttl)
