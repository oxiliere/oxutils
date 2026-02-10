from typing import Optional, Any
from uuid import UUID
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Count
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth import get_user_model

import structlog

from oxutils.mixins.services import BaseService
from oxutils.exceptions import NotFoundException
from .models import Grant, RoleGrant, Group, Role
from .utils import (
    assign_role, revoke_role,
    assign_group, revoke_group,
    override_grant
)
from .exceptions import (
    RoleNotFoundException,
    GroupNotFoundException,
    GrantNotFoundException,
    RoleGrantNotFoundException,
)

User = get_user_model()



logger = structlog.get_logger(__name__)



class PermissionService(BaseService):
    """
    Service pour la gestion des permissions.
    Encapsule la logique métier liée aux rôles, groupes et grants.
    """

    def inner_exception_handler(self, exc: Exception, logger):
        """
        Gère les exceptions spécifiques au service de permissions.
        Convertit les exceptions métier en exceptions HTTP appropriées.
        
        Args:
            exc: L'exception à gérer
            logger: Logger pour la journalisation
            
        Raises:
            APIException: Si l'exception est gérée
            Exception: Re-lève l'exception originale si non gérée
        """
        from oxutils.exceptions import APIException
        
        # Si c'est déjà une APIException (incluant nos exceptions personnalisées),
        # on la re-lève directement
        if isinstance(exc, APIException):
            raise exc
        
        # Convertir les exceptions Django DoesNotExist en exceptions HTTP appropriées
        from django.core.exceptions import ObjectDoesNotExist
        
        if isinstance(exc, ObjectDoesNotExist):
            # Déterminer le type d'objet pour un message plus précis
            exc_name = type(exc).__name__
            
            if 'Role' in exc_name:
                raise RoleNotFoundException(detail=str(exc))
            elif 'Group' in exc_name:
                raise GroupNotFoundException(detail=str(exc))
            elif 'Grant' in exc_name:
                raise GrantNotFoundException(detail=str(exc))
            elif 'RoleGrant' in exc_name:
                raise RoleGrantNotFoundException(detail=str(exc))
            else:
                # Exception générique pour les autres cas
                raise NotFoundException(detail=str(exc))
        
        # Pour toutes les autres exceptions, laisser le handler parent gérer
        raise exc

    def get_roles(self, app: Optional[str] = None):
        self.check_perm_application(app)

        if app:
            return Role.objects.filter(
                Q(app=app) |
                Q(app__isnull=True)
            )
        
        return Role.objects.all()

    def assign_role_to_user(
        self,
        user_id: int,
        role_slug: str,
        *,
        by_user: Optional[AbstractBaseUser] = None
    ) -> Role:
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
            user = User.objects.get(pk=user_id)
            role = Role.objects.get(slug=role_slug)
            
            assign_role(user, role_slug, by=by_user)
            
            grants_count = Grant.objects.filter(user=user, role=role).count()
            logger.info("role_assigned_to_user", user_id=user.pk, role=role_slug, grants_created=grants_count)
            
            return role
            
        except Role.DoesNotExist:
            raise RoleNotFoundException(detail=f"Le rôle '{role_slug}' n'existe pas")
        except User.DoesNotExist:
            raise NotFoundException(detail=f"L'utilisateur avec l'ID {user_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def revoke_role_from_user(
        self,
        user_id: int,
        role_slug: str
    ) -> None:
        """
        Révoque un rôle d'un utilisateur.
        
        Args:
            user: L'utilisateur dont on révoque le rôle
            role_slug: Le slug du rôle à révoquer
            
        Returns:
            Dictionnaire avec les informations de la révocation
        """
        try:
            user = User.objects.get(pk=user_id)
            deleted_count, _ = revoke_role(user, role_slug)
            
            logger.info("role_revoked_from_user", user_id=user.pk, role=role_slug, grants_deleted=deleted_count)
            
        except User.DoesNotExist:
            raise NotFoundException(detail=f"L'utilisateur avec l'ID {user_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def assign_group_to_user(
        self,
        user_id: int,
        group_slug: str,
        by_user: Optional[AbstractBaseUser] = None
    ) -> list[Role]:
        """
        Assigne tous les rôles d'un groupe à un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur à qui assigner le groupe
            group_slug: Le slug du groupe à assigner
            by_user: L'utilisateur qui effectue l'assignation (pour traçabilité)
            
        Returns:
            Liste des rôles du groupe
            
        Raises:
            NotFoundException: Si le groupe ou l'utilisateur n'existe pas
        """
        try:
            user = User.objects.get(pk=user_id)
            group = Group.objects.prefetch_related('roles').get(slug=group_slug)
            
            assign_group(user, group_slug, by=by_user)

            logger.info("group_assigned_to_user", user_id=user.pk, group=group_slug, roles_assigned=group.roles.count())
            
            return list(group.roles.all())
            
        except Group.DoesNotExist:
            raise GroupNotFoundException(detail=f"Le groupe '{group_slug}' n'existe pas")
        except User.DoesNotExist:
            raise NotFoundException(detail=f"L'utilisateur avec l'ID {user_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def revoke_group_from_user(
        self,
        user_id: int,
        group_slug: str
    ) -> None:
        """
        Révoque tous les rôles d'un groupe d'un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur dont on révoque le groupe
            group_slug: Le slug du groupe à révoquer
            
        Raises:
            NotFoundException: Si le groupe ou l'utilisateur n'existe pas
        """
        try:
            user = User.objects.get(pk=user_id)
            deleted_count, _ = revoke_group(user, group_slug)
            
            logger.info("group_revoked_from_user", user_id=user.pk, group=group_slug, grants_deleted=deleted_count)
            
        except User.DoesNotExist:
            raise NotFoundException(detail=f"L'utilisateur avec l'ID {user_id} n'existe pas")
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
                raise NotFoundException(
                    detail=f"Aucun grant trouvé pour l'utilisateur sur le scope '{scope}'"
                )
            
            override_grant(user, scope, remove_actions)
            
            # Vérifier si le grant existe toujours (peut avoir été supprimé)
            grant_still_exists = Grant.objects.filter(user=user, scope=scope).exists()
            
            logger.info("grant_modified", user_id=user.pk, scope=scope, removed_actions=remove_actions, grant_deleted=not grant_still_exists, grant_exists=grant_still_exists)
            
            return {
                "user_id": user.pk,
                "scope": scope,
                "removed_actions": remove_actions,
                "grant_deleted": not grant_still_exists,
                "message": "Grant modifié avec succès" if grant_still_exists else "Grant supprimé (plus d'actions)"
            }
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def check_perm_application(self, app: str | None) -> None:
        allowed_apps = getattr(settings, "ACCESS_APPLICATIONS", None)

        if app:
            if allowed_apps is None:
                logger.error("ACCESS_APPLICATIONS is missing in Django settings.", app=app)
                raise ValueError(_("Application is not allowed"))

            if app not in allowed_apps:
                    logger.error("Application is not allowed.", app=app)
                    raise ValueError(_("Application is not allowed"))
    
    def get_user_grants(
        self,
        user_id: UUID,
        scope: Optional[str] = None,
        app: Optional[str] = None,
    ) -> list[Grant]:
        """
        Récupère tous les grants d'un utilisateur.
        
        Args:
            user_id: L'ID de l'utilisateur dont on récupère les grants
            scope: Optionnel, filtre par scope
            
        Returns:
            Liste des grants de l'utilisateur
        """
        try:
            self.check_perm_application(app)    
            
            queryset = Grant.objects.filter(user__pk=user_id).select_related(
                'role',
                'group',
                'created_by',
            )
            
            if scope:
                queryset = queryset.filter(scope=scope)

            if app:
                queryset = queryset.filter(
                    Q(role__app=app) |
                    Q(group__app=app) |
                    Q(role__app__isnull=True) |
                    Q(group__app__isnull=True)
                )
            
            return list(queryset)
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def get_groups(self, app: Optional[str] | None = None):
        self.check_perm_application(app)

        qs = Group.objects.prefetch_related('user_groups', 'roles').annotate(
            member_count=Count('user_groups', distinct=True),
            role_count=Count('roles', distinct=True),
        ).all()
        
        if app:
            qs = qs.filter(
                Q(app=app) |
                Q(app__isnull=True)
            )
        
        return list(qs)

    def create_group(
        self,
        group_data
    ) -> Group:
        """
        Crée un nouveau groupe et lui assigne des rôles.
        
        Args:
            group_data: Données du groupe incluant:
                - slug: Identifiant unique du groupe
                - name: Nom du groupe
                - app: Application associée (optionnel)
                - roles: Liste optionnelle des slugs de rôles à assigner
            
        Returns:
            Le groupe créé
            
        Raises:
            DuplicateEntryException: Si le groupe existe déjà
            NotFoundException: Si un rôle n'existe pas
        """
        try:
            group = Group.objects.create(slug=group_data.slug, name=group_data.name, app=group_data.app)
            
            if group_data.roles:
                roles = Role.objects.filter(slug__in=group_data.roles)
                
                if roles.count() != len(group_data.roles):
                    found_slugs = set(roles.values_list('slug', flat=True))
                    missing_slugs = set(group_data.roles) - found_slugs
                    raise RoleNotFoundException(
                        detail=f"Rôles non trouvés: {list(missing_slugs)}"
                    )
                
                group.roles.set(roles)
            
            logger.info("group_created", slug=group_data.slug, name=group_data.name, role_slugs=group_data.roles, role_count=len(group_data.roles) if group_data.roles else 0)
            return group
            
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def get_role_grants(self, app: Optional[str] = None):
        self.check_perm_application(app)

        queryset = RoleGrant.objects.select_related('role', 'group').all()
        if app:
            queryset = queryset.filter(
                Q(role__app=app) |
                Q(group__app=app) |
                Q(role__app__isnull=True) |
                Q(group__app__isnull=True)
            )
        return list(queryset)

    @transaction.atomic
    def create_role_grant(
        self,
        grant_data
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
            role = Role.objects.get(slug=grant_data.role)
            
            role_grant = RoleGrant.objects.create(
                role=role,
                scope=grant_data.scope,
                actions=grant_data.actions,
                context=grant_data.context
            )
            
            logger.info("role_grant_created", role_slug=grant_data.role, scope=grant_data.scope, actions=grant_data.actions)
            
            return role_grant
            
        except Role.DoesNotExist:
            raise RoleNotFoundException(detail=f"Le rôle '{grant_data.role}' n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def update_grant(
        self,
        grant_id: int,
        grant_data
    ) -> Grant:
        """
        Met à jour un grant existant.
        
        Args:
            grant_id: ID du grant à mettre à jour
            grant_data: Schéma contenant les nouvelles données
            
        Returns:
            Le grant mis à jour
            
        Raises:
            GrantNotFoundException: Si le grant n'existe pas
        """
        try:
            grant = Grant.objects.get(pk=grant_id)
            
            if grant_data.actions is not None:
                grant.actions = grant_data.actions
            
            if grant_data.context is not None:
                grant.context = grant_data.context
            
            if grant_data.role is not None:
                try:
                    grant.role = Role.objects.get(slug=grant_data.role)
                except Role.DoesNotExist:
                    raise RoleNotFoundException(detail=f"Le rôle '{grant_data.role}' n'existe pas")
            
            grant.save()
            
            logger.info("grant_updated", grant_id=grant_id)
            
            return grant
            
        except Grant.DoesNotExist:
            raise GrantNotFoundException(detail=f"Le grant avec l'ID {grant_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def update_role_grant(
        self,
        grant_id: int,
        grant_data
    ) -> RoleGrant:
        """
        Met à jour un role grant existant.
        
        Args:
            grant_id: ID du role grant à mettre à jour
            grant_data: Schéma contenant les nouvelles données
            
        Returns:
            Le role grant mis à jour
            
        Raises:
            RoleGrantNotFoundException: Si le role grant n'existe pas
        """
        try:
            role_grant = RoleGrant.objects.get(pk=grant_id)
            
            if grant_data.actions is not None:
                role_grant.actions = grant_data.actions
            
            if grant_data.context is not None:
                role_grant.context = grant_data.context
            
            role_grant.save()
            
            logger.info("role_grant_updated", grant_id=grant_id)
            
            return role_grant
            
        except RoleGrant.DoesNotExist:
            raise RoleGrantNotFoundException(detail=f"Le role grant avec l'ID {grant_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)

    def delete_role_grant(
        self,
        grant_id: int
    ) -> None:
        """
        Supprime un role grant.
        
        Args:
            grant_id: ID du role grant à supprimer
            
        Raises:
            RoleGrantNotFoundException: Si le role grant n'existe pas
        """
        try:
            role_grant = RoleGrant.objects.get(pk=grant_id)
            role_grant.delete()
            
            logger.info("role_grant_deleted", grant_id=grant_id)
            
        except RoleGrant.DoesNotExist:
            raise RoleGrantNotFoundException(detail=f"Le role grant avec l'ID {grant_id} n'existe pas")
        except Exception as exc:
            self.exception_handler(exc, self.logger)
