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
    default_detail = _('Le rôle demandé n\'existe pas')


class GroupNotFoundException(NotFoundException):
    """Exception levée quand un groupe n'est pas trouvé."""
    default_detail = _('Le groupe demandé n\'existe pas')


class GrantNotFoundException(NotFoundException):
    """Exception levée quand un grant n'est pas trouvé."""
    default_detail = _('Le grant demandé n\'existe pas')


class RoleGrantNotFoundException(NotFoundException):
    """Exception levée quand un role grant n'est pas trouvé."""
    default_detail = _('Le role grant demandé n\'existe pas')


class RoleAlreadyAssignedException(DuplicateEntryException):
    """Exception levée quand un rôle est déjà assigné à un utilisateur."""
    default_detail = _('Ce rôle est déjà assigné à l\'utilisateur')


class GroupAlreadyAssignedException(DuplicateEntryException):
    """Exception levée quand un groupe est déjà assigné à un utilisateur."""
    default_detail = _('Ce groupe est déjà assigné à l\'utilisateur')


class InvalidActionsException(ValidationException):
    """Exception levée quand des actions invalides sont fournies."""
    default_detail = _('Les actions fournies sont invalides')


class InsufficientPermissionsException(PermissionDeniedException):
    """Exception levée quand l'utilisateur n'a pas les permissions suffisantes."""
    default_code = ExceptionCode.INSUFFICIENT_PERMISSIONS
    default_detail = _('Permissions insuffisantes pour effectuer cette action')


class RoleGrantConflictException(DuplicateEntryException):
    """Exception levée quand un role grant existe déjà pour ce rôle et scope."""
    default_detail = _('Un role grant existe déjà pour ce rôle et ce scope')


class GrantConflictException(DuplicateEntryException):
    """Exception levée quand un grant existe déjà pour cet utilisateur et scope."""
    default_detail = _('Un grant existe déjà pour cet utilisateur et ce scope')
