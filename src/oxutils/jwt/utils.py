from functools import wraps
import structlog
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from ninja_jwt.exceptions import InvalidToken



logger = structlog.getLogger("django")
User = get_user_model()


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
        request.user = User.objects.get(oxi_id=request.user.id)
    except User.DoesNotExist as exc:
        logger.exception('user_not_found', oxi_id=request.user.id, message=str(exc))
        raise InvalidToken()
