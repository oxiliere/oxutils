from allauth.mfa.adapter import get_adapter
from allauth.mfa.base.internal.flows import check_rate_limit, post_authentication
from allauth.mfa.models import Authenticator
from django.contrib.auth import get_user_model
from django.core import signing
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from ninja import Schema
from pydantic import ValidationInfo, model_validator

from oxutils.auth.mfa.utils import get_mfa_signing_salt, get_mfa_signing_ttl


class AuthenticateSchema(Schema):
    code: str
    key: str

    @model_validator(mode="after")
    def post_validation(self, info: ValidationInfo):
        try:
            key_payload = signing.loads(
                self.key, salt=get_mfa_signing_salt(), max_age=get_mfa_signing_ttl()
            )
        except signing.BadSignature:
            raise ValueError("Invalid MFA token")

        user_model = get_user_model()
        self._request = info.context["request"]
        self._request.user = get_object_or_404(user_model, pk=key_payload["uid"])

        clear_rl = check_rate_limit(self._request.user)

        for auth in Authenticator.objects.filter(user=self._request.user).exclude(
            type=Authenticator.Type.WEBAUTHN
        ):
            if auth.wrap().validate_code(self.code):
                self._authenticator = auth
                clear_rl()
                return self

        raise get_adapter().validation_error("incorrect_code")

    def authenticate(self):
        post_authentication(self._request, self._authenticator, reauthenticated=False)


class ReauthenticateSchema(Schema):
    code: str

    @model_validator(mode="after")
    def post_validation(self, info: ValidationInfo):
        self._request = info.context["request"]
        clear_rl = check_rate_limit(self._request.user)

        for auth in Authenticator.objects.filter(user=self._request.user).exclude(
            type=Authenticator.Type.WEBAUTHN
        ):
            if auth.wrap().validate_code(self.code):
                self._authenticator = auth
                clear_rl()
                return self

        raise get_adapter().validation_error("incorrect_code")

    def authenticate(self):
        post_authentication(self._request, self._authenticator, reauthenticated=True)
