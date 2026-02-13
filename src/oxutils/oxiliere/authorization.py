from django.conf import settings
from django.db import transaction
from oxutils.permissions.models import Grant, RoleGrant, Role
from oxutils.permissions.actions import ACTIONS
from oxutils.oxiliere.utils import get_tenant_user_model
from oxutils.oxiliere.models import BaseTenant


@transaction.atomic
def grant_manager_access_to_owners(tenant: BaseTenant):
    tenant_user_model = get_tenant_user_model()
    tenant_users = tenant_user_model.objects.select_related("user").filter(tenant=tenant, is_owner=True)

    access_scope = getattr(settings, 'ACCESS_MANAGER_SCOPE')
    access_role = getattr(settings, 'ACCESS_MANAGER_ROLE', None)

    role = None
    if access_role:
        try:
            role = Role.objects.get(slug=access_role)
        except Role.DoesNotExist:
            role = None

    role_grants = list(RoleGrant.objects.select_related(
        'role',
    ).filter(scope=access_scope))

    print("role_grants ========================", role_grants)

    
    bulk_grant = []

    if not role_grants:
        for tenant_user in tenant_users:
            bulk_grant.append(
                Grant(
                    user=tenant_user.user,
                    scope=access_scope,
                    role=role,
                    actions=ACTIONS,
                    context={},
                    user_group=None,
                    created_by=None,
                )
            )
    else:
        for tenant_user in tenant_users:
            for role_grant in role_grants:
                bulk_grant.append(
                    Grant(
                        user=tenant_user.user,
                        scope=role_grant.scope,
                        role=role_grant.role,
                        actions=role_grant.actions,
                        context=role_grant.context,
                        user_group=None,
                        created_by=None,
                    )
                )

    if bulk_grant:
        Grant.objects.bulk_create(bulk_grant)
