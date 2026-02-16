from django.utils.translation import gettext_lazy as _
from oxutils.exceptions import (
    APIException,
    NotFoundException,
    ValidationException,
    DuplicateEntryException,
    PermissionDeniedException,
    ExceptionCode
)


class RoleNotFoundException(NotFoundException):
    """Exception levée quand un rôle n'est pas trouvé."""
    default_detail = _('The requested role does not exist')


class GroupNotFoundException(NotFoundException):
    """Exception levée quand un groupe n'est pas trouvé."""
    default_detail = _('The requested group does not exist')


class GrantNotFoundException(NotFoundException):
    """Exception levée quand un grant n'est pas trouvé."""
    default_detail = _('The requested grant does not exist')


class RoleGrantNotFoundException(NotFoundException):
    """Exception levée quand un role grant n'est pas trouvé."""
    default_detail = _('The requested role grant does not exist')


class RoleAlreadyAssignedException(DuplicateEntryException):
    """Exception levée quand un rôle est déjà assigné à un utilisateur."""
    default_detail = _('This role is already assigned to the user')


class GroupAlreadyAssignedException(DuplicateEntryException):
    """Exception levée quand un groupe est déjà assigné à un utilisateur."""
    default_detail = _('This group is already assigned to the user')


class InvalidActionsException(ValidationException):
    """Exception levée quand des actions invalides sont fournies."""
    default_detail = _('The provided actions are invalid')


class InsufficientPermissionsException(PermissionDeniedException):
    """Exception levée quand l'utilisateur n'a pas les permissions suffisantes."""
    default_code = ExceptionCode.INSUFFICIENT_PERMISSIONS
    default_detail = _('Insufficient permissions to perform this action')


class RoleGrantConflictException(DuplicateEntryException):
    """Exception levée quand un role grant existe déjà pour ce rôle et scope."""
    default_detail = _('A role grant already exists for this role and scope')


class GrantConflictException(DuplicateEntryException):
    """Exception levée quand un grant existe déjà pour cet utilisateur et scope."""
    default_detail = _('A grant already exists for this user and scope')
