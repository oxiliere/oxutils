from django.conf import settings



CACHE_CHECK_PERMISSION = getattr(settings, 'CACHE_CHECK_PERMISSION', False)

if CACHE_CHECK_PERMISSION:
    from cacheops import cached_as
    from .models import Grant
    from .utils import check, any_action_check, any_permission_check

    @cached_as(Grant, timeout=60*15)
    def cache_check(user, scope, actions, role = None, **context):
        return check(user, scope, actions, role=role, **context)
    
    @cached_as(Grant, timeout=60*15)
    def cache_any_action_check(user, scope, required, role = None, **context):
        return any_action_check(user, scope, required, role=role, **context)
    
    @cached_as(Grant, timeout=60*15)
    def cache_any_permission_check(user, *str_perms):
        return any_permission_check(user, *str_perms)
else:
    from .utils import check, any_action_check, any_permission_check

    def cache_check(user, scope, actions, role = None, **context):
        return check(user, scope, actions, role=role, **context)
    
    def cache_any_action_check(user, scope, required, role = None, **context):
        return any_action_check(user, scope, required, role=role, **context)
    
    def cache_any_permission_check(user, *str_perms):
        return any_permission_check(user, *str_perms)
