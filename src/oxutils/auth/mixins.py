"""
Cookie token mixin with configurable security flags.
"""
from django.conf import settings

from oxutils.auth.constants import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE


def _cookie_http_only() -> bool:
    """Whether auth cookies should be HttpOnly (default: True)."""
    return getattr(settings, "AUTH_COOKIE_HTTP_ONLY", True)


def _cookie_secure() -> bool:
    """Whether auth cookies should be Secure (default: not DEBUG)."""
    if hasattr(settings, "AUTH_COOKIE_SECURE"):
        return settings.AUTH_COOKIE_SECURE
    return not settings.DEBUG if hasattr(settings, "DEBUG") else True


def _cookie_samesite() -> str:
    """SameSite policy for auth cookies (default: Lax)."""
    return getattr(settings, "AUTH_COOKIE_SAME_SITE", "Lax")


def _cookie_domain() -> str:
    """Domain for auth cookies."""
    return getattr(settings, "OXI_COOKIE_DOMAIN", None)


class CookieTokenMixin:
    def set_token_cookie(self, access_token: str, refresh_token: str):
        domain = _cookie_domain()
        secure = _cookie_secure()
        samesite = _cookie_samesite()
        httponly = _cookie_http_only()

        if getattr(settings, "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE", True):
            self.context.response.set_cookie(
                key=REFRESH_TOKEN_COOKIE,
                value=refresh_token,
                httponly=httponly,
                domain=domain,
                secure=secure,
                samesite=samesite,
            )

        self.context.response.set_cookie(
            key=ACCESS_TOKEN_COOKIE,
            value=access_token,
            httponly=httponly,
            domain=domain,
            secure=secure,
            samesite=samesite,
        )

    def remove_token_cookie(self):
        domain = _cookie_domain()
        samesite = _cookie_samesite()

        if getattr(settings, "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE", True):
            self.context.response.delete_cookie(
                key=REFRESH_TOKEN_COOKIE, domain=domain, samesite=samesite
            )

        self.context.response.delete_cookie(
            key=ACCESS_TOKEN_COOKIE, domain=domain, samesite=samesite
        )
