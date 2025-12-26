from typing import Optional, Any
from logging import Logger
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from oxutils.mixins.services import BaseService
from .models import Grant, RoleGrant, Group, Role
from .utils import assign_role, revoke_role, assign_group, override_grant, check
from .actions import expand_actions, collapse_actions


class PermissionService(BaseService):
    """
    Service pour la gestion des permissions.
    Encapsule la logique métier liée aux rôles, groupes et grants.
    """

    def assign_role_to_user(
        self,
        user: AbstractBaseUser,
        role_slug: str,
        *,
        by_user: Optional[AbstractBaseUser] = None
    ) -> dict[str, Any]:
        """
        Assigne un rôle à un utilisateur.
        
        Args:
            user: L'utilisateur à qui assigner le rôle
            role_slug: Le slug du rôle à assigner
            by_user: L'utilisateur qui effectue l'assignation (pour traçabilité)
            
        Returns:
            Dictionnaire avec les informations de l'assignation
            
        Raises:
            NotFoundException: Si le rôle n'existe pas
        """
        try:
            # Vérifier que le rôle existe
            role = Role.objects.get(slug=role_slug)
            
            # Assigner le rôle
            assign_role(user, role_slug, by=by_user)
            
            # Compter les grants créés
            grants_count = Grant.objects.filter(user=user, role=role).count()
            
            return {
                "user_id": user.pk,
                "role": role_slug,
                "grants_created": grants_count,
                "message": f"Rôle '{role_slug}' assigné avec succès"
            }
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def revoke_role_from_user(
        self,
        user: AbstractBaseUser,
        role_slug: str
    ) -> dict[str, Any]:
        """
        Révoque un rôle d'un utilisateur.
        
        Args:
            user: L'utilisateur dont on révoque le rôle
            role_slug: Le slug du rôle à révoquer
            
        Returns:
            Dictionnaire avec les informations de la révocation
        """
        try:
            deleted_count, _ = revoke_role(user, role_slug)
            
            return {
                "user_id": user.pk,
                "role": role_slug,
                "grants_deleted": deleted_count,
                "message": f"Rôle '{role_slug}' révoqué avec succès"
            }
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def assign_group_to_user(
        self,
        user: AbstractBaseUser,
        group_slug: str
    ) -> dict[str, Any]:
        """
        Assigne tous les rôles d'un groupe à un utilisateur.
        
        Args:
            user: L'utilisateur à qui assigner le groupe
            group_slug: Le slug du groupe à assigner
            
        Returns:
            Dictionnaire avec les informations de l'assignation
            
        Raises:
            NotFoundException: Si le groupe n'existe pas
        """
        try:
            group = Group.objects.prefetch_related('roles').get(slug=group_slug)
            roles_count = group.roles.count()
            
            assign_group(user, group_slug)
            
            return {
                "user_id": user.pk,
                "group": group_slug,
                "roles_assigned": roles_count,
                "message": f"Groupe '{group_slug}' assigné avec succès"
            }
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def override_user_grant(
        self,
        user: AbstractBaseUser,
        scope: str,
        remove_actions: list[str]
    ) -> dict[str, Any]:
        """
        Modifie un grant en retirant certaines actions.
        
        Args:
            user: L'utilisateur dont on modifie le grant
            scope: Le scope du grant à modifier
            remove_actions: Liste des actions à retirer
            
        Returns:
            Dictionnaire avec les informations de la modification
        """
        try:
            # Vérifier si le grant existe avant modification
            grant_exists = Grant.objects.filter(user=user, scope=scope).exists()
            
            if not grant_exists:
                from oxutils.exceptions import NotFoundException
                raise NotFoundException(
                    detail=f"Aucun grant trouvé pour l'utilisateur sur le scope '{scope}'"
                )
            
            override_grant(user, scope, remove_actions)
            
            # Vérifier si le grant existe toujours (peut avoir été supprimé)
            grant_still_exists = Grant.objects.filter(user=user, scope=scope).exists()
            
            return {
                "user_id": user.pk,
                "scope": scope,
                "removed_actions": remove_actions,
                "grant_deleted": not grant_still_exists,
                "message": "Grant modifié avec succès" if grant_still_exists else "Grant supprimé (plus d'actions)"
            }
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def check_permission(
        self,
        user: AbstractBaseUser,
        scope: str,
        required_actions: list[str],
        **context: Any
    ) -> bool:
        """
        Vérifie si un utilisateur possède les permissions requises.
        
        Args:
            user: L'utilisateur dont on vérifie les permissions
            scope: Le scope à vérifier
            required_actions: Liste des actions requises
            **context: Contexte additionnel pour filtrer les grants
            
        Returns:
            True si l'utilisateur possède les permissions, False sinon
        """
        try:
            return check(user, scope, required_actions, **context)
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def get_user_grants(
        self,
        user: AbstractBaseUser,
        scope: Optional[str] = None
    ) -> list[Grant]:
        """
        Récupère tous les grants d'un utilisateur.
        
        Args:
            user: L'utilisateur dont on récupère les grants
            scope: Optionnel, filtre par scope
            
        Returns:
            Liste des grants de l'utilisateur
        """
        try:
            queryset = Grant.objects.filter(user=user).select_related('role')
            
            if scope:
                queryset = queryset.filter(scope=scope)
            
            return list(queryset)
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def get_user_roles(self, user: AbstractBaseUser) -> list[str]:
        """
        Récupère tous les rôles uniques assignés à un utilisateur.
        
        Args:
            user: L'utilisateur dont on récupère les rôles
            
        Returns:
            Liste des slugs de rôles
        """
        try:
            role_slugs = Grant.objects.filter(
                user=user,
                role__isnull=False
            ).values_list('role__slug', flat=True).distinct()
            
            return list(role_slugs)
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def create_role(self, slug: str, name: str) -> Role:
        """
        Crée un nouveau rôle.
        
        Args:
            slug: Identifiant unique du rôle
            name: Nom du rôle
            
        Returns:
            Le rôle créé
            
        Raises:
            DuplicateEntryException: Si le rôle existe déjà
        """
        try:
            role = Role.objects.create(slug=slug, name=name)
            return role
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def create_group(
        self,
        slug: str,
        name: str,
        role_slugs: Optional[list[str]] = None
    ) -> Group:
        """
        Crée un nouveau groupe et lui assigne des rôles.
        
        Args:
            slug: Identifiant unique du groupe
            name: Nom du groupe
            role_slugs: Liste optionnelle des slugs de rôles à assigner
            
        Returns:
            Le groupe créé
            
        Raises:
            DuplicateEntryException: Si le groupe existe déjà
            NotFoundException: Si un rôle n'existe pas
        """
        try:
            group = Group.objects.create(slug=slug, name=name)
            
            if role_slugs:
                roles = Role.objects.filter(slug__in=role_slugs)
                
                if roles.count() != len(role_slugs):
                    found_slugs = set(roles.values_list('slug', flat=True))
                    missing_slugs = set(role_slugs) - found_slugs
                    from oxutils.exceptions import NotFoundException
                    raise NotFoundException(
                        detail=f"Rôles non trouvés: {list(missing_slugs)}"
                    )
                
                group.roles.set(roles)
            
            return group
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    @transaction.atomic
    def create_role_grant(
        self,
        role_slug: str,
        scope: str,
        actions: list[str],
        context: Optional[dict[str, Any]] = None
    ) -> RoleGrant:
        """
        Crée un role grant (template de permissions pour un rôle).
        
        Args:
            role_slug: Slug du rôle
            scope: Scope du grant
            actions: Liste des actions autorisées
            context: Contexte JSON optionnel
            
        Returns:
            Le role grant créé
            
        Raises:
            NotFoundException: Si le rôle n'existe pas
            DuplicateEntryException: Si le role grant existe déjà
        """
        try:
            role = Role.objects.get(slug=role_slug)
            
            role_grant = RoleGrant.objects.create(
                role=role,
                scope=scope,
                actions=actions,
                context=context or {}
            )
            
            return role_grant
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def get_role_grants(self, role_slug: str) -> list[RoleGrant]:
        """
        Récupère tous les grants d'un rôle.
        
        Args:
            role_slug: Slug du rôle
            
        Returns:
            Liste des role grants
            
        Raises:
            NotFoundException: Si le rôle n'existe pas
        """
        try:
            role = Role.objects.get(slug=role_slug)
            return list(RoleGrant.objects.filter(role=role))
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

