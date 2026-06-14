from ninja import ModelSchema

from oxutils.auth.tokens.models import (
    RefreshTokenWhitelistModel,
    GenericTokenModel
)


class RefreshTokenWhitelistSchema(ModelSchema):
    """
    User model w/o password
    """

    class Meta:
        model = RefreshTokenWhitelistModel
        exclude = ('id',)


class GenericTokenModelSchema(ModelSchema):
    """
    User model w/o password
    """

    class Meta:
        model = GenericTokenModel
        exclude = ('id',)
