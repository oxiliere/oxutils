from django.conf import settings



CACHE_CHECK_PERMISSION = getattr(settings, 'CACHE_CHECK_PERMISSION', False)

if CACHE_CHECK_PERMISSION:
    from cacheops import cached_as
    from .models import Grant
    from .utils import check

    @cached_as(Grant, timeout=60*5)
    def cache_check(user, scope, actions, group = None, **context):
        return check(user, scope, actions, group, **context)
else:
    from .utils import check

    def cache_check(user, scope, actions, group = None, **context):
        return check(user, scope, actions, group, **context)
