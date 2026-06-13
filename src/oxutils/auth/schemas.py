from typing import Any, Dict, Optional
from uuid import UUID

from allauth.mfa import app_settings as mfa_settings
from allauth.mfa.utils import is_mfa_enabled
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import AbstractUser
from django.core import signing
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext_lazy as _
from ninja import Schema
from ninja_extra import exceptions
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.schema import SCHEMA_INPUT, SchemaInputService, TokenObtainPairInputSchema
from pydantic import ValidationInfo, model_validator

from oxutils.auth.exceptions import IncorrectCredentials
from oxutils.auth.tokens.app_settings import RefreshToken
from oxutils.auth.tokens.models import RefreshTokenWhitelistModel
from oxutils.auth.tokens.utils import create_user_token, refresh_token
from oxutils.auth.utils import (
    allauth_authenticate,
    get_refresh_token,
    is_email_verified,
    populate_user,
    user_agent_dict,
    write_user_agent,
)

user_name_field = get_user_model().USERNAME_FIELD  # type: ignore


class BaseLoginOutputSchema(Schema):
    code: str

    def is_mfa_required(self):
        return self.code == "mfa_required"


class TokenObtainPairOutputSchema(BaseLoginOutputSchema):
    refresh: str
    access: str


class TokenObtainMFARequiredSchema(BaseLoginOutputSchema):
    key: str


class LoginSchema(TokenObtainPairInputSchema):
    @model_validator(mode="before")
    def validate_inputs(cls, values: SCHEMA_INPUT, info: ValidationInfo) -> dict:
        schema_input = SchemaInputService(values, cls.model_config)
        input_values = schema_input.get_values()

        if isinstance(input_values, dict):
            cls.validate_values(info.context.get("request"), values=input_values)
        return values

    @classmethod
    def validate_values(cls, request: HttpRequest, values: Dict) -> Dict:
        if user_name_field not in values and "password" not in values:
            raise exceptions.ValidationError(
                {
                    user_name_field: f"{user_name_field} is required",
                    "password": "password is required",
                }
            )

        if not values.get(user_name_field):
            raise exceptions.ValidationError({user_name_field: f"{user_name_field} is required"})

        if not values.get("password"):
            raise exceptions.ValidationError({"password": "password is required"})

        _user = allauth_authenticate(request=request, **values)

        cls._user = _user

        if not (_user is not None and _user.is_active):
            raise exceptions.AuthenticationFailed(cls._default_error_messages["no_active_account"])

        if not is_email_verified(_user):
            raise exceptions.AuthenticationFailed(cls._default_error_messages["email_not_verified"])

        return values

    @classmethod
    def get_token(cls, user: AbstractUser) -> Dict:
        request = getattr(cls, "_request", None)

        if is_mfa_enabled(user, mfa_settings.SUPPORTED_TYPES):
            from oxutils.auth.mfa.utils import get_mfa_signing_salt

            token = signing.dumps({"uid": str(user.pk)}, salt=get_mfa_signing_salt())

            return {"code": "mfa_required", "key": token}

        write_user_agent(request)
        refresh = create_user_token(user, request=request)

        return {"code": "logged_in", "refresh": str(refresh), "access": str(refresh.access_token)}

    def to_response_schema(self):
        data = self.get_response_schema_init_kwargs()
        _schema_type = TokenObtainPairOutputSchema

        if data["code"] == "mfa_required":
            _schema_type = TokenObtainMFARequiredSchema

        return _schema_type(**data)


class SendVerificationEmailSchema(Schema):
    email: str

    def send_verification_email(self, request: HttpRequest):
        from oxutils.auth.emails.services import UserEmailService

        email_service = UserEmailService()

        try:
            request.user = get_user_model().objects.get(email=self.email)
        except get_user_model().DoesNotExist:
            return False

        email_service.sync_user_email_address(request)

        return email_service.send_verification_email(request, self.email)


class ReauthenticatePasswordSchema(Schema):
    password: str

    def authenticate(self, request: HttpRequest):
        if not request.user.check_password(self.password):
            raise IncorrectCredentials()

        _refresh_token = get_refresh_token(request)

        if not _refresh_token:
            raise InvalidToken

        ctx = {"force": True, **user_agent_dict(request)}
        tokens = refresh_token(_refresh_token, context=ctx)

        return TokenObtainPairOutputSchema(
            code="logged_in", refresh=tokens["refresh"], access=tokens["access"]
        )


class RemoveRefreshTokenSchema(Schema):
    refresh: str
    user: Optional[UUID] = None

    @model_validator(mode="after")
    @transaction.atomic
    def post_validate(self, info: ValidationInfo) -> Dict[str, str]:
        refresh = RefreshToken(self.refresh)  # The token is verified
        user_id = str(self.user) if self.user else str(info.context.get("user", ""))
        if not user_id or "session" not in refresh.payload:
            raise InvalidToken()
        if not constant_time_compare(user_id, str(refresh.payload["user_id"])):
            raise InvalidToken()
        query = RefreshTokenWhitelistModel.objects.filter(
            Q(jti=refresh.payload["jti"]) | Q(session=refresh.payload["session"])
        )
        if not query.count() > 0:
            raise InvalidToken()
        query.delete()
        return {}


class BaseChangePasswordSchema(Schema):
    new_password1: str
    new_password2: str

    def validate_password_change(
        self,
        user,
    ) -> Dict[str, Any]:
        """
        Validate password change data and return validation results.

        Args:
            user: The authenticated user

        Returns:
            Dict containing validation results and any errors

        Raises:
            exceptions.ValidationError: If validation fails
        """
        if hasattr(self, "old_password_field_enabled"):
            old_password_field_enabled = self.old_password_field_enabled
        else:
            old_password_field_enabled = getattr(settings, "OLD_PASSWORD_FIELD_ENABLED", True)

        errors = {}

        # Validate old password if required
        if old_password_field_enabled:
            if not self.old_password:
                errors["old_password"] = [_("This field is required.")]
            elif not user.check_password(self.old_password):
                errors["old_password"] = [
                    _("Your old password was entered incorrectly. Please enter it again.")
                ]

        # Validate new passwords using Django's SetPasswordForm
        form_data = {
            "new_password1": self.new_password1,
            "new_password2": self.new_password2,
        }

        set_password_form = SetPasswordForm(user=user, data=form_data)

        if not set_password_form.is_valid():
            errors.update(set_password_form.errors)

        if errors:
            raise exceptions.ValidationError(errors)

        return {"form": set_password_form, "old_password_field_enabled": old_password_field_enabled}

    @transaction.atomic
    def change_user_password(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Change user password and handle session management.

        Args:
            user: The authenticated user
            request: HTTP request object

        Returns:
            Dict containing success status and message
        """
        # Validate the password change
        user = request.user
        validation_result = self.validate_password_change(user)
        set_password_form = validation_result["form"]

        # Save the new password
        set_password_form.save()

        # Handle logout on password change setting
        logout_on_password_change = getattr(settings, "LOGOUT_ON_PASSWORD_CHANGE", True)

        if logout_on_password_change:
            # Remove all refresh tokens except current session
            if (
                hasattr(request, "auth")
                and hasattr(request.auth, "token_session")
                and request.auth.token_session
            ):
                RefreshTokenWhitelistModel.objects.filter(user=request.user.id).exclude(
                    session=request.auth.token_session
                ).delete()
        else:
            # Keep user logged in by updating session auth hash
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, user)

        return self.get_response(logout_on_password_change)

    @model_validator(mode="after")
    def post_validate(self, info: ValidationInfo):
        request = info.context.get("request")
        populate_user(request)
        self.change_user_password(request)
        return self

    def get_response(self, logout_on_password_change=True):
        return {
            "success": True,
            "message": str(_("Password changed successfully.")),
            "logout_required": logout_on_password_change,
        }


class PasswordChangeSchema(BaseChangePasswordSchema):
    """Schema for password change requests."""

    old_password: Optional[str] = None


class PasswordChangeResponseSchema(Schema):
    """Schema for password change response."""

    success: bool
    message: str


class TokenRefreshInputSchema(Schema):
    refresh: Optional[str] = None


class TokenRefreshOutputSchema(Schema):
    refresh: str
    access: str


class TokenRefreshSchema(Schema):
    refresh: str
    access: Optional[str] = None  # if none try on cookies

    @model_validator(mode="after")
    @transaction.atomic
    def post_validate(self, info: ValidationInfo) -> Any:
        return refresh_token(self.refresh, info.context)
