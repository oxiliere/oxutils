from django.conf import settings
from django.db import transaction
from oxutils.permissions.actions import ACTIONS
from oxutils.permissions.models import Grant, Group, UserGroup
from oxutils.oxiliere.utils import get_tenant_user_model
from oxutils.oxiliere.models import BaseTenant


@transaction.atomic
def grant_manager_access_to_owners(tenant: BaseTenant):
    tenant_user_model = get_tenant_user_model()
    tenant_users = tenant_user_model.objects.select_related("user").filter(tenant=tenant, is_owner=True)

    access_scope = getattr(settings, 'ACCESS_MANAGER_SCOPE')
    access_group = getattr(settings, 'ACCESS_MANAGER_GROUP')

    if access_group:
        try:
            group = Group.objects.get(slug=access_group)
        except Group.DoesNotExist:
            group = None

    bulk_grant = []
    for tenant_user in tenant_users:
        if group:
            user_group, _ = UserGroup.objects.get_or_create(
                user=tenant_user.user,
                group=group,
            )
        else:
            user_group = None
        
        bulk_grant.append(
            Grant(
                user=tenant_user.user,
                scope=access_scope,
                role=None,
                actions=ACTIONS,
                context={},
                user_group=user_group,
                created_by=None,
            )
        )

    Grant.objects.bulk_create(bulk_grant)
