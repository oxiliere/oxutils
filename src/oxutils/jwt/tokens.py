from django.conf import settings
from ninja_jwt.tokens import Token, AccessToken
from ninja_jwt.backends import TokenBackend
from ninja_jwt.settings import api_settings
from datetime import timedelta
from oxutils.settings import oxi_settings




__all__ = [
    'AccessToken',
    'OrganizationAccessToken',
]



token_backend = TokenBackend(
    algorithm='HS256',
    signing_key=settings.SECRET_KEY,
    verifying_key="",
    audience=None,
    issuer=None,
    jwk_url=None,
    leeway=api_settings.LEEWAY,
    json_encoder=api_settings.JSON_ENCODER,
)



class OxilierServiceToken(Token):
    token_type = oxi_settings.jwt_service_token_key
    lifetime = timedelta(minutes=oxi_settings.jwt_service_token_lifetime)


    @classmethod
    def for_service(cls, payload: dict = {}) -> Token:
        token = cls()

        for key, value in payload.items():
            token[key] = value

        return token


class OrganizationAccessToken(Token):
    token_type = oxi_settings.jwt_org_access_token_key
    lifetime = timedelta(minutes=oxi_settings.jwt_org_access_token_lifetime)

    @classmethod
    def for_tenant(cls, tenant) -> Token:
        token = cls()
        token.payload['tenant_id'] = str(tenant.id)
        token.payload['oxi_id'] = str(tenant.oxi_id)
        token.payload['schema_name'] = str(tenant.schema_name)
        token.payload['subscription_plan'] = str(tenant.subscription_plan)
        token.payload['subscription_status'] = str(tenant.subscription_status)
        token.payload['subscription_end_date'] = str(tenant.subscription_end_date)
        token.payload['status'] = str(tenant.status)

        return token

    @property
    def token_backend(self):
        return token_backend

    def get_token_backend(self):
        # Backward compatibility.
        return self.token_backend
