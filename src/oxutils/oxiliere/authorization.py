from django.conf import settings
from django.db import transaction

from oxutils.oxiliere.models import BaseTenant
from oxutils.oxiliere.utils import get_tenant_user_model
from oxutils.permissions.models import RoleGrant
from oxutils.permissions.utils import assign_role


@transaction.atomic
def grant_manager_access_to_owners(tenant: BaseTenant):
    tenant_user_model = get_tenant_user_model()
    tenant_users = tenant_user_model.objects.select_related("user").filter(
        tenant=tenant, is_owner=True
    )

    access_scope = settings.ACCESS_MANAGER_SCOPE

    # Vérifier qu'il y a des RoleGrants pour ce scope
    role_grants = list(RoleGrant.objects.filter(scope=access_scope))

    if not role_grants:
        return

    for tenant_user in tenant_users:
        for grant in role_grants:
            assign_role(
                user=tenant_user.user, role=grant.role, scope=grant.scope, by=None, user_group=None
            )
