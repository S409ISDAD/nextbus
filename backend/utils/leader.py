import uuid

INSTANCE_ID = str(uuid.uuid4())


def acquire_leader(redis, channel, key, ttl=10):
    lock_key = f"leader:{channel}:{key}"
    return redis.set(lock_key, INSTANCE_ID, nx=True, ex=ttl)


def refresh_leader(redis, channel, key, ttl=10):
    lock_key = f"leader:{channel}:{key}"
    current = redis.get(lock_key)
    if current == INSTANCE_ID:
        redis.expire(lock_key, ttl)
