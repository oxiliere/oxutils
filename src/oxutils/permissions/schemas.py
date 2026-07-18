from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from django.conf import settings
from ninja import Schema
from pydantic import field_validator

from oxutils.oxiliere.schemas import UserSchema

from .actions import get_all_valid_actions


def _get_valid_scope_keys() -> set[str]:
    """Return the set of valid scope keys from ACCESS_SCOPES."""
    scopes = getattr(settings, "ACCESS_SCOPES", [])
    if not isinstance(scopes, list):
        return set()
    keys: set[str] = set()
    for entry in scopes:
        if isinstance(entry, dict):
            keys.add(entry.get("key", ""))
        else:
            keys.add(str(entry))
    return keys


def validate_actions_list(actions: list[str]) -> list[str]:
    """
    Valide qu'une liste d'actions contient uniquement des actions déclarées
    dans le preset ``PERMISSION_PRESET["actions"]``.

    Si aucun preset d'actions n'est défini, la validation est permissive
    (toutes les actions sont acceptées).

    Args:
        actions: Liste des actions à valider

    Returns:
        La liste d'actions si valide

    Raises:
        ValueError: Si des actions invalides sont présentes
    """
    if not actions:
        raise ValueError("Les actions ne peuvent pas être vides")

    valid_actions = get_all_valid_actions()

    # Permissive mode: if no actions are defined in the preset, accept anything
    if not valid_actions:
        return actions

    invalid_actions = [a for a in actions if a not in valid_actions]
    if invalid_actions:
        raise ValueError(
            f"Actions invalides: {invalid_actions}. "
            f"Actions déclarées dans le preset: {sorted(valid_actions)}"
        )
    return actions


class RoleSchema(Schema):
    """
    Schéma pour un rôle.
    """

    slug: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleSimpleSchema(Schema):
    """
    Schéma pour un rôle.
    """

    slug: str
    name: str

    class Config:
        from_attributes = True


class RoleCreateSchema(Schema):
    """
    Schéma pour la création d'un rôle.
    """

    slug: str
    name: str


class RoleUpdateSchema(Schema):
    """
    Schéma pour la mise à jour d'un rôle.
    """

    name: Optional[str] = None


class GroupSchema(Schema):
    """
    Schéma pour un groupe.
    """

    slug: str
    name: str
    app: Optional[str] = None
    roles: list[RoleSimpleSchema] = []
    member_count: int = 0
    role_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimpleGroupSchema(Schema):
    slug: str
    name: str


class GroupCreateSchema(Schema):
    """
    Schéma pour la création d'un groupe.
    """

    name: str
    app: Optional[str] = None
    roles: list[str] = []


class GroupUpdateSchema(Schema):
    """
    Schéma pour la mise à jour d'un groupe.
    """

    name: Optional[str] = None
    roles: Optional[list[str]] = None


class GroupMemberSchema(Schema):
    """
    Schéma pour un membre d'un groupe.
    """

    user: UserSchema
    group_id: str
    created_at: Optional[datetime] = None


class RoleGrantSchema(Schema):
    """
    Schéma pour un role grant.
    """

    id: int
    role: RoleSimpleSchema
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}

    class Config:
        from_attributes = True


class RoleGrantCreateSchema(Schema):
    """
    Schéma pour la création d'un role grant.
    """

    role: str
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Valide que toutes les actions sont valides."""
        return validate_actions_list(v)


class RoleGrantUpdateSchema(Schema):
    """
    Schéma pour la mise à jour d'un role grant.
    """

    actions: Optional[list[str]] = None
    context: Optional[dict[str, Any]] = None

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Valide que toutes les actions sont valides."""
        if v is not None:
            return validate_actions_list(v)
        return v


class GrantSchema(Schema):
    """
    Schéma pour un grant utilisateur.
    """

    id: int
    user_id: UUID
    role: RoleSimpleSchema
    locked: bool = False
    group: Optional[SimpleGroupSchema] = None
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @staticmethod
    def resolve_group(obj):
        return obj.user_group.group if obj.user_group else None


class GrantCreateSchema(Schema):
    """
    Schéma pour la création d'un grant utilisateur.
    """

    user_id: UUID
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}
    role: str

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Valide que toutes les actions sont valides."""
        return validate_actions_list(v)


class GrantUpdateSchema(Schema):
    """
    Schéma pour la mise à jour d'un grant utilisateur.
    """

    actions: Optional[list[str]] = None
    context: Optional[dict[str, Any]] = None
    role: Optional[str] = None

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Valide que toutes les actions sont valides."""
        if v is not None:
            return validate_actions_list(v)
        return v


class PermissionCheckSchema(Schema):
    """
    Schéma pour une requête de vérification de permissions.
    """

    user_id: UUID
    scope: str
    required_actions: list[str]
    context: dict[str, Any] = {}

    @field_validator("required_actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Valide que toutes les actions sont valides."""
        return validate_actions_list(v)


class PermissionCheckResponseSchema(Schema):
    """
    Schéma pour la réponse d'une vérification de permissions.
    """

    allowed: bool
    user_id: UUID
    scope: str
    required_actions: list[str]


class AssignRoleSchema(Schema):
    """
    Schéma pour assigner un rôle à un utilisateur.
    """

    user_id: UUID
    role: str
    scope: str

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        """Valide que le scope est valide."""
        if v not in _get_valid_scope_keys():
            raise ValueError(f"Invalid scope '{v}'")
        return v


class OverrideGrantSchema(Schema):
    """
    Schéma pour modifier un grant utilisateur.
    """

    user_id: UUID
    scope: str
    role: str
    actions: list[str]

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        """Valide que le scope est valide."""
        if v not in _get_valid_scope_keys():
            raise ValueError(f"Invalid scope '{v}'")
        return v

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Valide que toutes les actions sont valides."""
        return validate_actions_list(v)


class RevokeRoleSchema(Schema):
    """
    Schéma pour révoquer un rôle d'un utilisateur.
    """

    user_id: UUID
    scope: str
    role: str

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        """Valide que le scope est valide."""
        if v not in _get_valid_scope_keys():
            raise ValueError(f"Invalid scope '{v}'")
        return v


class AssignGroupSchema(Schema):
    """
    Schéma pour assigner un groupe à un utilisateur.
    """

    user_id: UUID
    group: str


class RevokeGroupSchema(Schema):
    """
    Schéma pour révoquer un groupe d'un utilisateur.
    """

    user_id: UUID
    group: str


class GroupSyncResponseSchema(Schema):
    """
    Schéma pour la réponse de la synchronisation d'un groupe.
    """

    users_synced: int
    grants_updated: int


class PresetLoadResponseSchema(Schema):
    """
    Schéma pour la réponse du chargement d'un preset.
    """

    roles_created: int
    groups_created: int
    role_grants_created: int
    message: str = "Preset chargé avec succès"


class ActionLabelSchema(Schema):
    """
    Schéma pour une action avec son label traduit.
    """

    key: str
    label: str


class ScopeActionsResponseSchema(Schema):
    """
    Schéma pour la réponse listant les actions d'un scope avec leurs labels.
    """

    scope: str
    actions: list[ActionLabelSchema]


class ScopeSchema(Schema):
    """
    Schéma pour un scope avec son label (affichage frontend).
    """

    key: str
    label: str
