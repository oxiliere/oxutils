import os

TENANT_LIMIT_SET_CALLS = True

CACHEOPS_PREFIX = 'oxutils.oxiliere.cacheops.cacheops_prefix'


REDIS_URLS = os.getenv("REDIS_URLS", "redis://127.0.0.1:6379").split(",")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URLS,
        'KEY_FUNCTION': 'django_tenants.cache.make_key',
        'REVERSE_KEY_FUNCTION': 'django_tenants.cache.reverse_key',
    }
}
