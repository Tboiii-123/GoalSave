from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def get_or_set_cache(key, fetch_data, timeout=300):
    """
    Retrieve data from cache or fetch and cache it.

    Args:
        key (str): Cache key.
        fetch_data (callable): Function that returns the data if cache misses.
        timeout (int): Cache timeout in seconds.
    """

    try:
        data = cache.get(key)
    except Exception:
        logger.exception("Cache GET failed for key=%s", key)
        return fetch_data()

    if data is not None:
        logger.info("Cache HIT for key=%s", key)
        return data

    logger.info("Cache MISS for key=%s", key)

    data = fetch_data()

    try:
        cache.set(key, value=data, timeout=timeout)
        logger.info("Cached key=%s for %s seconds", key, timeout)
    except Exception:
        logger.exception("Cache SET failed for key=%s", key)

    return data



# Inavlidate cache

def invalidate_cache(key):
    try:
        cache.delete(key)
        logger.info("Cache invalidated: %s", key)
    except Exception:
        logger.exception("Cache DELETE failed for key=%s", key)



def invalidate_withdrawal_cache():
    clear_cache_pattern("admin:withdrawals:*")




def clear_cache_pattern(pattern):
    try:
        cache.delete_pattern(pattern)
        logger.info(
            "Cache pattern invalidated: %s",
            pattern
        )
    except Exception:
        logger.exception(
            "Cache pattern DELETE failed: %s",
            pattern
        )