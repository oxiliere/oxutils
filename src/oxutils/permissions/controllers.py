from typing import List, Optional
from uuid import UUID
from django.conf import settings
from django.http import HttpRequest
from ninja_extra import (
    api_controller,
    ControllerBase,
    http_get,
    http_post,
    http_put,
    http_delete,
)
from ninja_extra.permissions import IsAuthenticated
from . import schemas
from .services import PermissionService
from .perms import access_manager




@api_controller(
    "/access",
    permissions=[
        IsAuthenticated & access_manager('r')
    ]
)
class PermissionController(ControllerBase):
    """
    Contrôleur pour la gestion des permissions, rôles et groupes.
    """
    service = PermissionService()

    @http_get('/scopes', response=List[str])
    def list_scopes(self):
        return getattr(settings, 'ACCESS_SCOPES', [])

    @http_get("/roles", response=List[schemas.RoleSchema])
    def list_roles(self):
        """
        Liste tous les rôles.
        """
        return self.service.get_roles()

    # Groupes
    @http_post(
        "/groups", 
        response=schemas.GroupSchema,
        permissions=[
            IsAuthenticated & access_manager('w')
        ]
    )
    def create_group(self, group_data: schemas.GroupCreateSchema):
        """
        Crée un nouveau groupe de rôles.
        """
        return self.service.create_group(group_data)

    @http_get(
        "/groups", 
        response=List[schemas.GroupSchema],
    )
    def list_groups(self, app: Optional[str] = None):
        """
        Liste tous les groupes de rôles.
        """
        return self.service.get_groups(app)

    @http_get(
        "/groups/{group_slug}", 
        response=schemas.GroupSchema,
    )
    def get_group(self, group_slug: str):
        """
        Récupère un groupe par son slug.
        """
        return self.service.get_group(group_slug)

    @http_put(
        "/groups/{group_slug}", 
        response=schemas.GroupSchema,
        permissions=[
            IsAuthenticated & access_manager('ru')
        ]
    )
    def update_group(self, group_slug: str, group_data: schemas.GroupUpdateSchema):
        """
        Met à jour un groupe existant.
        """
        return self.service.update_group(
            group_slug,
            group_data.dict(exclude_unset=True, exclude={"roles"}),
            group_data.roles
        )

    @http_delete(
        "/groups/{group_slug}", 
        response={
            204: None
        },
        permissions=[
            IsAuthenticated & access_manager('d')
        ]
    )
    def delete_group(self, group_slug: str):
        """
        Supprime un groupe.
        """
        self.service.delete_group(group_slug)
        return 204, None

    @http_get(
        "/groups/{group_slug}/members",
        response=List[schemas.GroupMemberSchema],
        permissions=[
            IsAuthenticated & access_manager('r')
        ]
    )
    def get_group_members(self, group_slug: str):
        """
        Récupère les membres d'un groupe.
        """
        return self.service.get_group_members(group_slug)

    # Rôles des utilisateurs    
    @http_post(
        "/users/assign-role",
        response=schemas.RoleSchema,
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def assign_role_to_user(self, data: schemas.AssignRoleSchema, request: HttpRequest):
        """
        Assigne un rôle à un utilisateur.
        """
        return self.service.assign_role_to_user(
            user_id=data.user_id,
            role_slug=data.role,
            scope=data.scope,
            by_user=request.user if request.user.is_authenticated else None
        )

    @http_post(
        "/users/revoke-role", 
        response={
            204: None
        },
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def revoke_role_from_user(self, data: schemas.RevokeRoleSchema):
        """
        Révoque un rôle d'un utilisateur.
        """
        self.service.revoke_role_from_user(
            user_id=data.user_id,
            role_slug=data.role,
            scope=data.scope
        )
        return None

    @http_post(
        "/users/override-grant",
        response={
            204: None
        },
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def override_grant_for_user(self, data: schemas.OverrideGrantSchema):
        """
        Modifie un grant utilisateur en définissant de nouvelles actions.
        Si actions est vide, le grant est supprimé.
        """
        self.service.override_grant_for_user(
            user_id=data.user_id,
            scope=data.scope,
            actions=data.actions,
            role=data.role
        )
        return None

    @http_post(
        "/users/assign-group",
        response=List[schemas.RoleSchema],
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def assign_group_to_user(self, data: schemas.AssignGroupSchema, request: HttpRequest):
        """
        Assigne un groupe de rôles à un utilisateur.
        """
        return self.service.assign_group_to_user(
            user_id=data.user_id,
            group_slug=data.group,
            by_user=request.user if request.user.is_authenticated else None
        )

    @http_post(
        "/users/revoke-group", 
        response={
            204: None
        },
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def revoke_group_from_user(self, data: schemas.RevokeGroupSchema):
        """
        Révoque un groupe de rôles d'un utilisateur.
        """
        self.service.revoke_group_from_user(
            user_id=data.user_id,
            group_slug=data.group
        )
        return None

    @http_get(
        "/users/{user_id}/grants",
        response=List[schemas.GrantSchema],
        permissions=[
            IsAuthenticated & access_manager('r')
        ]
    )
    def get_user_grants(self, user_id: UUID, scope: Optional[str] = None, app: Optional[str] = None):
        """
        Récupère tous les grants d'un utilisateur.
        """
        return self.service.get_user_grants(user_id=user_id, scope=scope, app=app)

    @http_get(
        "/users/{user_id}/groups",
        response=List[schemas.GroupSchema],
        permissions=[
            IsAuthenticated & access_manager('r')
        ]
    )
    def get_user_groups(self, user_id: UUID):
        """
        Récupère tous les groupes d'un utilisateur.
        """
        return self.service.get_user_groups(user_id=user_id)

    @http_put(
        "/grants/{grant_id}", 
        response=schemas.GrantSchema,
        permissions=[
            IsAuthenticated & access_manager('ru')
        ]
    )
    def update_grant(self, grant_id: int, grant_data: schemas.GrantUpdateSchema):
        """
        Met à jour une permission personnalisée.
        """
        return self.service.update_grant(grant_id, grant_data)

    # Role Grants
    @http_post(
        "/role-grants", 
        response=schemas.RoleGrantSchema,
        permissions=[
            IsAuthenticated & access_manager('rw')
        ]
    )
    def create_role_grant(self, grant_data: schemas.RoleGrantCreateSchema):
        """
        Crée une nouvelle permission pour un rôle.
        """
        return self.service.create_role_grant(grant_data)

    @http_get(
        "/role-grants", 
        response=List[schemas.RoleGrantSchema],
    )
    def list_role_grants(self, app: Optional[str] = None):
        """
        Liste les permissions de rôles, avec filtrage optionnel par application.
        """
        return self.service.get_role_grants(app)

    @http_put(
        "/role-grants/{grant_id}", 
        response=schemas.RoleGrantSchema,
        permissions=[
            IsAuthenticated & access_manager('ru')
        ]
    )
    def update_role_grant(self, grant_id: int, grant_data: schemas.RoleGrantUpdateSchema):
        """
        Met à jour une permission de rôle.
        """
        return self.service.update_role_grant(grant_id, grant_data)

    @http_delete(
        "/role-grants/{grant_id}/", 
        response={
            204: None
        },
        permissions=[
            IsAuthenticated & access_manager('d')
        ]
    )
    def delete_role_grant(self, grant_id: int):
        """
        Supprime une permission de rôle.
        """
        self.service.delete_role_grant(grant_id)
        return None
