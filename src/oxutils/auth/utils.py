import logging
import time
from functools import wraps
from importlib import import_module
from typing import Dict, Optional

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.internal.flows.reauthentication import get_reauthentication_flows
from allauth.account.models import EmailAddress
from allauth.account.signals import authentication_step_completed
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django_user_agents.utils import get_user_agent as get_user_agent_django
from ninja_jwt.exceptions import InvalidToken
from ninja_jwt.settings import api_settings as ninja_jwt_settings
from ninja_jwt.utils import datetime_from_epoch

from oxutils.auth.constants import (
    REFRESH_TOKEN_COOKIE,
    TEMPLATE_PATHS,
)
from oxutils.auth.exceptions import (
    IncorrectCredentials,
    NotVerifiedEmail,
    ReauthenticationRequired,
)

logger = logging.getLogger("django")
User = get_user_model()


def import_callable(path_or_callable):
    """
    Convert a Python path string to a callable object or return the input if already callable.

    Args:
        path_or_callable (str|callable): Either a Python path string (module.attribute)
                                        or an already callable object

    Returns:
        callable: The resolved callable object

    Raises:
        TypeError: If input is a string but not a valid Python path
    """
    if callable(path_or_callable):
        return path_or_callable

    if not isinstance(path_or_callable, str):
        raise TypeError(f"Expected a callable or dotted path string, got {type(path_or_callable)}")

    package, attr = path_or_callable.rsplit(".", 1)
    return getattr(import_module(package), attr)


def get_client_ip(request):
    """
    Extract client IP address from request metadata.

    Priority:

        1. X-Forwarded-For header (first entry if multiple)
        2. REMOTE_ADDR meta value

    Args:
        request (HttpRequest): Django request object

    Returns:
        str: Client IP address or None if not found
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(f):
    """
    Decorator that adds user agent and IP information to the request object.

    Stores:
    - user_agent: Parsed user agent details
    - ip: Client IP address

    Args:
        f (function): View method to decorate

    Returns:
        function: Decorated view method
    """

    @wraps(f)
    def user_agent(self, request, *args, **kwargs):
        write_user_agent(request)
        return f(self, request, *args, **kwargs)

    return user_agent


def write_user_agent(request):
    """
    Write the user_agent on Request Object

    """
    if not request:
        return

    if getattr(settings, "JWT_ALLAUTH_COLLECT_USER_AGENT", False):
        request.user_agent = get_user_agent_django(request)
        request.ip = get_client_ip(request)
    else:
        request.user_agent = None
        request.ip = None


def user_agent_dict(request):
    """
    Generate a detailed dictionary of user agent information.

    Includes:

        - Browser details (name, version)
        - OS details (name, version)
        - Device information (family, brand, model)
        - Network information (IP address)
        - Device type flags (mobile, tablet, PC, bot)

    Args:
        request (HttpRequest): Django request object

    Returns:
        dict: Structured user agent details. Empty dict if no request.
    """
    if request is None:
        return {}
    if not hasattr(request, "user_agent") or request.user_agent is None:
        return {}

    return {
        "browser": request.user_agent.browser.family,
        "browser_version": request.user_agent.browser.version_string,
        "os": request.user_agent.os.family,
        "os_version": request.user_agent.os.version_string,
        "device": request.user_agent.device.family,
        "device_brand": request.user_agent.device.brand,
        "device_model": request.user_agent.device.model,
        "ip": request.ip,
        "is_mobile": request.user_agent.is_mobile,
        "is_tablet": request.user_agent.is_tablet,
        "is_pc": request.user_agent.is_pc,
        "is_bot": request.user_agent.is_bot,
    }


sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        "password", "old_password", "new_password1", "new_password2", "password1", "password2"
    )
)


def get_template_path(constant, default):
    """
    Get template path from settings using TEMPLATE_PATHS configuration.

    Args:
        constant (str): Key to look up in TEMPLATE_PATHS setting
        default (str): Default path if not found in settings

    Returns:
        str: Configured template path or default value
    """
    templates_path_dict = getattr(settings, TEMPLATE_PATHS, {})
    if isinstance(templates_path_dict, dict):
        return templates_path_dict.get(constant, default)
    return default


def is_email_verified(user, raise_exception=False):
    """
    Check if user has a verified email address.

    Args:
        user (User): User object to check
        raise_exception (bool): Whether to raise NotVerifiedEmail if unverified

    Returns:
        bool: True if verified, False otherwise

    Raises:
        NotVerifiedEmail: If raise_exception=True and email is unverified
    """
    verify = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"

    if verify and not EmailAddress.objects.filter(user=user.id, verified=True).exists():
        if raise_exception:
            raise NotVerifiedEmail()
        return False
    return True


def allauth_authenticate(**kwargs):
    """
    Authenticate user using allauth's adapter with enhanced verification.

    Args:
        **kwargs: Authentication credentials (typically username/email + password)

    Returns:
        User: Authenticated user object

    Raises:
        IncorrectCredentials: If authentication fails
        NotVerifiedEmail: If email is not verified
    """
    user = get_adapter().authenticate(**kwargs)
    if user is None:
        raise IncorrectCredentials()
    is_email_verified(user, raise_exception=True)
    return user


def allauth_record_authentication(request, user, method, **extra_data):
    """Here we keep a log of all authentication methods used within the current
    session.  Important to note is that having entries here does not imply that
    a user is fully signed in. For example, consider a case where a user
    authenticates using a password, but fails to complete the 2FA challenge.
    Or, a user successfully signs in into an inactive account or one that still
    needs verification. In such cases, ``request.user`` is still anonymous, yet,
    we do have an entry here.

    Example data::

        {'method': 'password',
         'at': 1701423602.7184925,
         'username': 'john.doe'}

        {'method': 'socialaccount',
         'at': 1701423567.6368647,
         'provider': 'amazon',
         'uid': 'amzn1.account.K2LI23KL2LK2'}

        {'method': 'mfa',
         'at': 1701423602.6392953,
         'id': 1,
         'type': 'totp'}

    """

    data = {
        "method": method,
        "at": time.time(),
    }
    for k, v in extra_data.items():
        if v is not None:
            data[k] = v

    authentication_step_completed.send(
        sender=user.__class__, request=request, method=method, user=user, **extra_data
    )


def did_recently_authenticate(request: HttpRequest) -> bool:
    if request.user.is_anonymous:
        return False
    if not get_reauthentication_flows(request.user):
        return True

    user = get_token_user(request)
    cat_claim = getattr(user, "token_created_at", None)
    if not cat_claim:
        return False

    try:
        authenticated_at = datetime_from_epoch(cat_claim)
        time_diff = time.time() - authenticated_at.timestamp()
        timeout = allauth_settings.REAUTHENTICATION_TIMEOUT
        return time_diff < timeout
    except (ValueError, TypeError, AttributeError) as e:
        # Log the error for debugging but don't fail the authentication
        # Return False to be safe - require reauthentication
        return False


def raise_if_reauthentication_required(request: HttpRequest) -> None:
    if not did_recently_authenticate(request):
        raise ReauthenticationRequired()


def load_user(f):
    """
    Decorator that loads the complete user object from the database for stateless JWT authentication.
    This is necessary because JWT tokens only contain the user ID, and the full user object
    might be needed in the view methods.

    Usage:

    .. code-block:: python

        @load_user
        def my_view_method(self, *args, **kwargs):
            # self.request.user will be the complete user object
            pass
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        populate_user(self.context.request)
        res = f(self, *args, **kwargs)
        return res

    return wrapper


def populate_user(request: HttpRequest):
    if isinstance(request.user, User):
        return

    try:
        request.user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        raise InvalidToken()


def get_token_user(request: HttpRequest):
    if isinstance(request.user, ninja_jwt_settings.TOKEN_USER_CLASS):
        return request.user

    return request.token_user


def get_refresh_token(request: HttpRequest) -> Optional[str]:
    if getattr(settings, "JWT_ALLAUTH_REFRESH_TOKEN_AS_COOKIE", True) and request.COOKIES.get(
        REFRESH_TOKEN_COOKIE
    ):
        return request.COOKIES.get(REFRESH_TOKEN_COOKIE)

    elif request.headers.get("Authorization"):
        auth_value = request.headers.get("Authorization")
        if not auth_value:
            return None
        parts = auth_value.split(" ")

        if parts[0].lower() != "bearer":
            if settings.DEBUG:
                logger.warning("Unexpected auth scheme received")
            return None
        return " ".join(parts[1:])
    return None


def format_confirm_email_url(key: Optional[str] = None):
    """Format the email confirmation URL for the SPA frontend."""
    if not key:
        return ""

    from urllib.parse import quote

    frontend_urls: Dict[str, str] = getattr(settings, "ACCOUNT_FRONTEND_URLS", {})
    url_template = frontend_urls.get("account_confirm_email", "")

    return url_template.format(key=quote(key, safe=""))


def format_reset_password_url(uidb64: Optional[str] = None, token: Optional[str] = None):
    """Format the password reset URL for the SPA frontend."""
    if not uidb64 or not token:
        return ""

    from urllib.parse import quote

    frontend_urls: Dict[str, str] = getattr(settings, "ACCOUNT_FRONTEND_URLS", {})
    url_template = frontend_urls.get("account_reset_password", "")

    return url_template.format(uid=quote(uidb64, safe=""), token=quote(token, safe=""))
