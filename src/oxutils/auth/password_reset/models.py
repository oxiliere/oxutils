from typing import Union

from django.utils.functional import cached_property
from ninja_jwt.models import TokenUser

from oxutils.auth.constants import FOR_USER


class SetPasswordTokenUser(TokenUser):
    @cached_property
    def id(self) -> Union[int, str]:
        return self.token[FOR_USER]
