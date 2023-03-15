import random

from django.core.cache import cache

from django.conf import settings

TTL = settings.REDIS_CACHE_TTL


def get(key):
    return cache.get(key)


def set(key, value):
    cache.set(key, value)


def fetch_aot(key, expiry_gap_ms):
    ttl_ms = cache.pttl(key)  # pttl은 millisecond 단위

    if ttl_ms - (random() * expiry_gap_ms) > 0:
        return cache.get(key)

    return None


def get_with_update_ttl(key):
    """"""

    value = cache.get(key)
    if value:
        cache.expire(key, TTL)  # reset ttl

    print(f"{key} hit = {True if value else False}")
    return value
