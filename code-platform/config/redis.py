import random

from django.core.cache import cache
from django.conf import settings

TTL = settings.REDIS_CACHE_TTL


def get(key):
    return cache.get(key)


def set(key, value, timeout=None):
    timeout = timeout if timeout else TTL
    cache.set(key, value, timeout)


def fetch_aot(key, expiry_gap_ms):
    """
    from nhn blog,
    https://meetup.nhncloud.com/posts/251
    """
    ttl_ms = cache.pttl(key)  # pttl은 millisecond 단위

    if ttl_ms - (random() * expiry_gap_ms) > 0:
        return cache.get(key)

    return None
