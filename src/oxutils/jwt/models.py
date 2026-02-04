from uuid import UUID
from django.utils.functional import cached_property
from ninja_jwt.models import TokenUser as DefaultTonkenUser
from ninja_jwt.settings import api_settings

import structlog
from .tokens import OrganizationAccessToken



logger = structlog.get_logger(__name__)


class TenantUser:
    def __init__(
        self,
        oxi_id: str | None = None,
        id: str | None = None,
        is_owner: bool = False,
        is_admin: bool = False,
        status: str | None = None,
    ):
        self.oxi_id = oxi_id
        self.id = id
        self.is_owner = is_owner
        self.is_admin = is_admin
        self.status = status

    def __bool__(self):
        return self.status == 'active'

    def is_active(self):
        return self.status == 'active'


class TokenTenant:

    def __init__(
        self,
        schema_name: str,
        tenant_id: str,
        oxi_id: str,
        subscription_plan: str,
        subscription_status: str,
        subscription_end_date: str | None = None,
        status: str = 'active',
        user: TenantUser | None = None,
        ):
        self.schema_name = schema_name
        self.id = tenant_id
        self.oxi_id = oxi_id
        self.subscription_plan = subscription_plan
        self.subscription_status = subscription_status
        self.subscription_end_date = subscription_end_date
        self.status = status
        self.user = user

    def __str__(self):
        return f"{self.schema_name} - {self.oxi_id}"

    @property
    def pk(self):
        return self.id

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_deleted(self):
        return self.status == 'deleted'

    def __bool__(self):
        return self.status == 'active'

    @property
    def is_admin_user(self):
        if self.user:
            return self.user.is_admin
        return False

    @property
    def is_owner_user(self):
        if self.user:
            return self.user.is_owner
        return False

    @property
    def is_tenant_user(self):
        if self.user:
            return self.user.is_active()
        return False

    def get_tenant_type(self):
        return self.subscription_status

    @classmethod
    def for_token(cls, token):
        try:
            token_obj = OrganizationAccessToken(token=token)

            # set the tenant user
            if 'tenant_user_id' in token_obj and token_obj.get('tenant_user_id'):
                user = TenantUser(
                    oxi_id=token_obj.get('tenant_user_oxi_id'),
                    id=token_obj.get('tenant_user_id'),
                    is_owner=token_obj.get('tenant_user_is_owner'),
                    is_admin=token_obj.get('tenant_user_is_admin'),
                    status=token_obj.get('tenant_user_status'),
                )
            else:
                user = TenantUser()
            
            tenant = cls(
                schema_name=token_obj['schema_name'],
                tenant_id=token_obj['tenant_id'],
                oxi_id=token_obj['oxi_id'],
                subscription_plan=token_obj['subscription_plan'],
                subscription_status=token_obj['subscription_status'],
                subscription_end_date=token_obj.get('subscription_end_date'),
                status=token_obj['status'],
                user=user,
            )
            
            return tenant
        except Exception:
            logger.exception('Failed to create TokenTenant from token', token=token)
            return None

    @classmethod
    def from_db(cls, tenant) -> 'TokenTenant':
        if not tenant:
            raise ValueError('Tenant is required')

        if hasattr(tenant, 'user') and tenant.user:
            user = TenantUser(
                oxi_id=tenant.user.user.oxi_id,
                id=tenant.user.id,
                is_owner=tenant.user.is_owner,
                is_admin=tenant.user.is_admin,
                status=tenant.user.status,
            )
        else:
            user = TenantUser()
            
        return cls(
            schema_name=tenant.schema_name,
            tenant_id=tenant.id,
            oxi_id=tenant.oxi_id,
            subscription_plan=tenant.subscription_plan,
            subscription_status=tenant.subscription_status,
            subscription_end_date=tenant.subscription_end_date,
            status=tenant.status,
            user=user,
        )

    def __repr__(self):
        return f"TokenTenant(schema_name='{self.schema_name}', oxi_id='{self.oxi_id}', status='{self.status}')"


class TokenUser(DefaultTonkenUser):
    @cached_property
    def id(self):
        return UUID(self.token[api_settings.USER_ID_CLAIM])

    @property
    def oxi_id(self):
        # for compatibility with the User model
        return self.id

    @cached_property
    def token_created_at(self):
        return self.token.get('cat', None)

    @cached_property
    def token_session(self):
        return self.token.get('session', None)
