from typing import Optional
from uuid import UUID 
from ninja import Schema
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.db import transaction
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model
from oxutils.oxiliere.utils import (
    get_tenant_user_model,
)
from oxutils.oxiliere.authorization import grant_manager_access_to_owners
import structlog

logger = structlog.get_logger(__name__)



def get_tenant_schema() -> 'TenantSchema':
    if hasattr(settings, 'OX_TENANT_SCHEMA'):
        try:
            return import_string(settings.OX_TENANT_SCHEMA)
        except ImportError as e:
            raise ImproperlyConfigured(
                f"Error: OX_TENANT_SCHEMA import error: {settings.OX_TENANT_SCHEMA}, please check your settings"
            ) from e
    return TenantSchema


class TenantSchema(Schema):
    name: str
    oxi_id: str
    subscription_plan: Optional[str]
    subscription_status: Optional[str]
    subscription_end_date: Optional[str]
    status: Optional[str]


class TenantOwnerSchema(Schema):
    oxi_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str


class UserSchema(Schema):
    oxi_id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    is_active: bool
    photo: Optional[str] = None


class TenantUserListSchema(Schema):
    user: UserSchema
    is_owner: bool
    is_admin: bool
    status: str
    is_active: bool


class TenantUserDetailSchema(Schema):
    user: UserSchema
    is_owner: bool
    is_admin: bool
    status: str

class UpdateTenantUserSchema(Schema):
    is_admin: Optional[bool] = None
    is_owner: Optional[bool] = None
    status: Optional[str] = None


class SetAdminSchema(Schema):
    is_admin: bool


class SetOwnerSchema(Schema):
    is_owner: bool


def get_tenant_user_list_schema() -> type[Schema]:
    if hasattr(settings, 'OX_TENANT_USER_LIST_SCHEMA'):
        try:
            return import_string(settings.OX_TENANT_USER_LIST_SCHEMA)
        except ImportError as e:
            raise ImproperlyConfigured(
                f"Error: OX_TENANT_USER_LIST_SCHEMA import error: {settings.OX_TENANT_USER_LIST_SCHEMA}, please check your settings"
            ) from e
    return TenantUserListSchema


def get_tenant_user_detail_schema() -> type[Schema]:
    if hasattr(settings, 'OX_TENANT_USER_DETAIL_SCHEMA'):
        try:
            return import_string(settings.OX_TENANT_USER_DETAIL_SCHEMA)
        except ImportError as e:
            raise ImproperlyConfigured(
                f"Error: OX_TENANT_USER_DETAIL_SCHEMA import error: {settings.OX_TENANT_USER_DETAIL_SCHEMA}, please check your settings"
            ) from e
    return TenantUserDetailSchema


class CreateTenantSchema(Schema):
    tenant: TenantSchema
    owner: TenantOwnerSchema


    @transaction.atomic
    def create_tenant(self):
        UserModel = get_user_model()
        TenantModel = get_tenant_model()
        TenantUserModel = get_tenant_user_model()

        if TenantModel.objects.filter(oxi_id=self.tenant.oxi_id).exists():
            logger.info("tenant_exists", oxi_id=self.tenant.oxi_id)
            raise ValueError("Tenant with oxi_id {} already exists".format(self.tenant.oxi_id))

        user, _ = UserModel.objects.get_or_create(
            oxi_id=self.owner.oxi_id,
            defaults={
                'id': self.owner.oxi_id,
                'email': self.owner.email,
                'first_name': self.owner.first_name,
                'last_name': self.owner.last_name
            }
        )
        
        tenant = TenantModel.objects.create(
            name=self.tenant.name,
            schema_name=self.tenant.oxi_id,
            oxi_id=self.tenant.oxi_id,
            subscription_plan=self.tenant.subscription_plan,
            subscription_status=self.tenant.subscription_status,
            subscription_end_date=self.tenant.subscription_end_date,
        )
        
        TenantUserModel.objects.create(
            tenant=tenant,
            user=user,
            is_owner=True,
            is_admin=True,
        )

        grant_manager_access_to_owners(tenant)
        logger.info("tenant_created", oxi_id=self.tenant.oxi_id)
        return tenant
