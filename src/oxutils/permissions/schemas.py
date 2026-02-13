from typing import Any, Optional
from datetime import datetime
from uuid import UUID
from ninja import Schema
from oxutils.oxiliere.schemas import UserSchema
from pydantic import field_validator

from .actions import ACTIONS


def validate_actions_list(actions: list[str]) -> list[str]:
    """
    Valide qu'une liste d'actions contient uniquement des actions valides.
    
    Args:
        actions: Liste des actions à valider
        
    Returns:
        La liste d'actions si valide
        
    Raises:
        ValueError: Si des actions invalides sont présentes
    """
    invalid_actions = [a for a in actions if a not in ACTIONS]
    if invalid_actions:
        raise ValueError(
            f"Actions invalides: {invalid_actions}. "
            f"Actions valides: {ACTIONS}"
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
    
    @field_validator('actions')
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
    
    @field_validator('actions')
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
    role: Optional[RoleSimpleSchema] = None
    group: Optional[str] = None
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @staticmethod
    def resolve_group(obj):
        return obj.user_group.group.slug if obj.user_group else None


class GrantCreateSchema(Schema):
    """
    Schéma pour la création d'un grant utilisateur.
    """
    user_id: UUID
    scope: str
    actions: list[str]
    context: dict[str, Any] = {}
    role: Optional[str] = None
    
    @field_validator('actions')
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
    
    @field_validator('actions')
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
    
    @field_validator('required_actions')
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
    by_user_id: Optional[UUID] = None


class RevokeRoleSchema(Schema):
    """
    Schéma pour révoquer un rôle d'un utilisateur.
    """
    user_id: UUID
    role: str


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


class OverrideGrantSchema(Schema):
    """
    Schéma pour modifier un grant en retirant des actions.
    """
    user_id: UUID
    scope: str
    remove_actions: list[str]
    
    @field_validator('remove_actions')
    @classmethod
    def validate_actions(cls, v: list[str]) -> list[str]:
        """Valide que toutes les actions sont valides."""
        return validate_actions_list(v)


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
