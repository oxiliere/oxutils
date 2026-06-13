import hashlib
from uuid import uuid4
from typing import Optional, Any
from datetime import datetime
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.tokens import RefreshToken as DefaultRefreshToken
from ninja_jwt.utils import datetime_to_epoch


from oxutils.auth.tokens.models import GenericTokenModel, RefreshTokenWhitelistModel
from oxutils.auth.utils import user_agent_dict




class RefreshToken(DefaultRefreshToken):

    def __init__(self, token: Optional[Any] = None, verify: bool = True) -> None:
        super().__init__(token, verify)
        self.set_cat()  # type: ignore

    def set_session(self, id_=None):
        """
        Unique identifier of the session associated to the refresh token.
        """
        if id_ is None:
            id_ = uuid4().hex

        if not self.payload.get('session'):
            self.payload['session'] = id_

    def set_user_role(self, user):
        self.payload['role'] = user.role

    def set_cat(self, claim: str = "cat", at_time: Optional[datetime] = None, force: bool = False) -> None:
        """
        Set the created_at time if is not present on payload

        """
        if self.payload.get(claim, None) and not force:
            return

        if at_time is None:
            at_time = self.current_time

        self.payload[claim] = datetime_to_epoch(at_time)

    @classmethod
    def for_user(cls, user, request=None, enabled=True):
        """
        Return
        ------
        RefreshToken

        """
        token = super().for_user(user)
        token.set_session()  # type: ignore
        token.set_user_role(user)  # type: ignore
        # Store the token in the database

        RefreshTokenWhitelistModel.objects.create(**{
            'user': user,
            'jti': token.payload['jti'],
            'user_id': user.id,
            'enabled': enabled,
            'session': token.payload['session'],
            **user_agent_dict(request)
        })
        return token


class GenericToken(PasswordResetTokenGenerator):

    def __init__(self, purpose, request=None):
        super().__init__()
        self.request = request
        self.purpose = purpose

    def make_token(self, user):
        token = super().make_token(user)
        hashed_token = hashlib.sha256(str(token).encode()).hexdigest()
        try:
            # Create the token model instance directly
            GenericTokenModel.objects.create(
                token=hashed_token,
                user=user,
                purpose=self.purpose,
                **user_agent_dict(self.request)
            )
            # remove existing tokens for the same purpose
            GenericTokenModel.objects.filter(user=user, purpose=self.purpose).exclude(token=hashed_token).delete()
        except Exception as e:
            raise InvalidToken(str(e))
        return token

    def check_token(self, user, token):
        result = super().check_token(user, token)
        if result:
            hashed_token = hashlib.sha256(str(token).encode()).hexdigest()
            if GenericTokenModel.objects.filter(token=hashed_token, purpose=self.purpose).count() == 0:
                return False
            GenericTokenModel.objects.filter(token=hashed_token, purpose=self.purpose).delete()
        return result
