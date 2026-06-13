"""
MFA utilities – signing salt and TTL configuration.
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_mfa_signing_salt() -> str:
    """
    Returns the MFA signing salt from Django settings.

    Must be explicitly configured via MFA_SIGNING_SALT in production.
    Raises ImproperlyConfigured if not set and DEBUG is False.
    """
    salt = getattr(settings, "MFA_SIGNING_SALT", None)
    if salt is None:
        if not getattr(settings, "DEBUG", True):
            raise ImproperlyConfigured(
                "MFA_SIGNING_SALT must be set in production. "
                "Use a long, random string unique to your deployment."
            )
        # Dev fallback — never use in production
        return "mfa-login-required-dev-only"
    return salt


def get_mfa_signing_ttl() -> int:
    """Returns the MFA signing TTL in seconds (default: 300)."""
    return getattr(settings, "MFA_SIGNING_TTL", 300)
