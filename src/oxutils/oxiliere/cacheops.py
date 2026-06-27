from cacheops import cached
from django.db import connection

# ── Tenant token TTL ──────────────────────────────────────────────

TENANT_TOKEN_TTL = 3600  # 60 minutes


def cacheops_prefix(query):
    if connection.schema_name:
        return '%s:' % connection.schema_name
    return 'default:'


# ── Tenant token cache (cacheops @cached pattern) ──────────────────

@cached(timeout=TENANT_TOKEN_TTL)
def get_cached_tenant_token(oxi_id: str, user_id: str):
    """Return the tenant DB object for *oxi_id* + *user_id*, fetching on miss.

    The returned tenant has ``.user`` pre-attached (the matching
    *TenantUser* row).  Cacheops caches the result automatically.
    Raises ``ObjectDoesNotExist`` when the tenant or tenant-user
    is not found, so the miss is **not** cached.
    """
    from django.core.exceptions import ObjectDoesNotExist
    from django_tenants.utils import get_tenant_model

    TenantModel = get_tenant_model()

    try:
        tenant = TenantModel.objects.get(oxi_id=oxi_id)
    except TenantModel.DoesNotExist as ex:
        raise ObjectDoesNotExist(f"tenant not found: {oxi_id}") from ex

    try:
        tenant_user = tenant.users.select_related("user").get(user__pk=user_id)
    except (ObjectDoesNotExist, ValueError) as ex:
        raise ObjectDoesNotExist(f"tenant_user not found: {oxi_id}/{user_id}") from ex

    tenant.user = tenant_user
    return tenant


def delete_cached_tenant_token(oxi_id: str, user_id: str) -> None:
    """Remove the cached tenant (e.g. on tenant-switch or logout)."""
    get_cached_tenant_token.invalidate(oxi_id, user_id)
