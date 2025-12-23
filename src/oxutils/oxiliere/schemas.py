from typing import Optional
from uuid import UUID 
from ninja import Schema
from django.db import transaction
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model
from oxutils.oxiliere.models import TenantUser
from oxutils.oxiliere.utils import oxid_to_schema_name
import structlog

logger = structlog.get_logger(__name__)


class TenantSchema(Schema):
    name: str
    oxi_id: str
    subscription_plan: Optional[str]
    subscription_status: Optional[str]
    subscription_end_date: Optional[str]
    status: Optional[str]


class TenantOwnerSchema(Schema):
    oxi_id: UUID
    email: str


class CreateTenantSchema(Schema):
    tenant: TenantSchema
    owner: TenantOwnerSchema


    @transaction.atomic
    def create_tenant(self):
        UserModel = get_user_model()
        TenantModel = get_tenant_model()

        if TenantModel.objects.filter(oxi_id=self.tenant.oxi_id).exists():
            logger.info("tenant_exists", oxi_id=self.tenant.oxi_id)
            raise ValueError("Tenant with oxi_id {} already exists".format(self.tenant.oxi_id))

        user, _ = UserModel.objects.get_or_create(
            oxi_id=self.owner.oxi_id,
            defaults={
                'email': self.owner.email,
            }
        )
        
        tenant = TenantModel.objects.create(
            name=self.tenant.name,
            schema_name=oxid_to_schema_name(self.tenant.oxi_id),
            oxi_id=self.tenant.oxi_id,
            subscription_plan=self.tenant.subscription_plan,
            subscription_status=self.tenant.subscription_status,
            subscription_end_date=self.tenant.subscription_end_date,
        )
        
        TenantUser.objects.create(
            tenant=tenant,
            user=user,
            is_owner=True,
            is_admin=True,
        )

        logger.info("tenant_created", oxi_id=self.tenant.oxi_id)
        return tenant
