from django.conf import settings

from oxutils.auth.tokens.tokens import RefreshToken as DefaultRefreshToken
from oxutils.auth.utils import import_callable

RefreshToken = import_callable(getattr(settings, 'JWT_ALLAUTH_REFRESH_TOKEN', DefaultRefreshToken))
