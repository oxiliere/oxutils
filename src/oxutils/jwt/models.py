# TokenTenant model
import structlog
from .tokens import OrganizationAccessToken



logger = structlog.get_logger(__name__)


class TokenTenant:

    def __init__(
        self,
        schema_name: str,
        tenant_id: int,
        oxi_id: str,
        subscription_plan: str,
        subscription_status: str,
        status: str,
        ):
        self.schema_name = schema_name
        self.id = tenant_id
        self.oxi_id = oxi_id
        self.subscription_plan = subscription_plan
        self.subscription_status = subscription_status
        self.status = status

    def __str__(self):
        return f"{self.schema_name} - {self.oxi_id}"

    @property
    def pk(self):
        return self.id

    @classmethod
    def for_token(cls, token):
        try:
            token_obj = OrganizationAccessToken(token=token)
            tenant = cls(
                schema_name=token_obj['schema_name'],
                tenant_id=token_obj['tenant_id'],
                oxi_id=token_obj['oxi_id'],
                subscription_plan=token_obj['subscription_plan'],
                subscription_status=token_obj['subscription_status'],
                status=token_obj['status'],
            )
            return tenant
        except Exception:
            logger.exception('Failed to create TokenTenant from token', token=token)
            return None
