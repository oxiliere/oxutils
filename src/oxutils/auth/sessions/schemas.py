from typing import Optional

from ninja import ModelSchema

from oxutils.auth.tokens.models import RefreshTokenWhitelistModel


class UserSession(ModelSchema):
    """Schema for user session information"""

    is_current: Optional[bool] = False

    class Meta:
        model = RefreshTokenWhitelistModel
        exclude = (
            "jti",
            "user",
        )
