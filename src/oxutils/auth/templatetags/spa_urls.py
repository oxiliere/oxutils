from typing import Optional

from django import template

from oxutils.auth.utils import format_confirm_email_url, format_reset_password_url

register = template.Library()


@register.simple_tag
def spa_url(url_type: str, uidb64: Optional[str] = None, key: Optional[str] = None):
    if url_type == "confirm_email":
        return format_confirm_email_url(key)
    elif url_type == "reset_password":
        return format_reset_password_url(uidb64, key)
    else:
        raise ValueError("Invalid URL Type.")
