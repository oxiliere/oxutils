from uuid import UUID

from django.utils.functional import cached_property
from ninja_jwt.models import TokenUser as DefaultTonkenUser
from ninja_jwt.settings import api_settings


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
        return self.token.get("cat", None)

    @cached_property
    def token_session(self):
        return self.token.get("session", None)
