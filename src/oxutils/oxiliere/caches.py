from django.conf import settings
from cacheops import cached_as, cached
from oxutils.oxiliere.utils import get_tenant_model, get_tenant_user_model




TenantModel = get_tenant_model()
TenantUserModel = get_tenant_user_model()


@cached_as(TenantModel, timeout=60*15)
def get_tenant_by_oxi_id(oxi_id: str):
    return TenantModel.objects.get(oxi_id=oxi_id)


@cached_as(TenantModel, timeout=60*15)
def get_tenant_by_schema_name(schema_name: str):
    return TenantModel.objects.get(schema_name=schema_name)


@cached_as(TenantUserModel, timeout=60*15)
def get_tenant_user(oxi_org_id: str, oxi_user_id: str):
    return TenantUserModel.objects.get(
        tenant__oxi_id=oxi_org_id,
        user__oxi_id=oxi_user_id
    )

@cached(timeout=60*15)
def get_system_tenant():
    from oxutils.oxiliere.utils import oxid_to_schema_name

    system_schema_name = oxid_to_schema_name(
        getattr(settings, 'OXI_SYSTEM_TENANT', 'tenant_oxisystem')
    )
    return get_tenant_model().objects.get(schema_name=system_schema_name)
