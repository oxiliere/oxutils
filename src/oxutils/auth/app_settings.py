from django.conf import settings

from oxutils.auth.password_reset.schemas import PasswordResetSchema as DefaultPasswordResetSchema
from oxutils.auth.registration.schemas import RegisterSchema as DefaultRegisterSchema
from oxutils.auth.schemas import (
    LoginSchema as DefaultLoginSchema,
)
from oxutils.auth.schemas import (
    PasswordChangeSchema as DefaultPasswordChangeSchema,
)
from oxutils.auth.utils import import_callable

schemas = getattr(settings, "JWT_ALLAUTH_SCHEMAS", {})

LoginSerializer = import_callable(schemas.get("LOGIN_SCHEMA", DefaultLoginSchema))

PasswordResetSerializer = import_callable(
    schemas.get("PASSWORD_RESET_SCHEMA", DefaultPasswordResetSchema)
)

PasswordChangeSerializer = import_callable(
    schemas.get("PASSWORD_CHANGE_SCHEMA", DefaultPasswordChangeSchema)
)

RegisterSerializer = import_callable(schemas.get("REGISTER_SCHEMA", DefaultRegisterSchema))
