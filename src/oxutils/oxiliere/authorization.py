from django.db import transaction

from oxutils.oxiliere.models import BaseTenant
from oxutils.oxiliere.utils import get_tenant_user_model
from oxutils.permissions.models import RoleGrant
from oxutils.permissions.utils import assign_role


@transaction.atomic
def grant_manager_access_to_owners(tenant: BaseTenant):
    """
    Grant **all** configured permissions to every tenant owner.

    Idempotent — can be called multiple times without creating duplicates.
    Uses :func:`assign_role` which performs an upsert per (user, scope, role).
    """
    tenant_user_model = get_tenant_user_model()
    tenant_users = tenant_user_model.objects.select_related("user").filter(
        tenant=tenant, is_owner=True
    )

    role_grants = list(RoleGrant.objects.select_related("role").all())

    if not role_grants:
        return

    for tenant_user in tenant_users:
        for rg in role_grants:
            assign_role(
                user=tenant_user.user,
                role=rg.role.slug,
                scope=rg.scope,
                by=None,
                user_group=None,
            )
