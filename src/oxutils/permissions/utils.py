from typing import Optional, Any
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.models import AbstractBaseUser

from .models import Grant, RoleGrant, Group, UserGroup, Role
from .actions import expand_actions
from .exceptions import (
    RoleNotFoundException,
    GroupNotFoundException,
    GrantNotFoundException,
    GroupAlreadyAssignedException
)




@transaction.atomic
def assign_role(
    user: AbstractBaseUser,
    role: str,
    *,
    by: Optional[AbstractBaseUser] = None,
    user_group: Optional[UserGroup] = None
) -> None:
    """
    Assigne un rôle à un utilisateur en créant ou mettant à jour les grants correspondants.
    
    Args:
        user: L'utilisateur à qui assigner le rôle
        role: Le slug du rôle à assigner
        by: L'utilisateur qui effectue l'assignation (pour traçabilité)
        user_group: Le UserGroup associé si le rôle est assigné via un groupe
        
    Raises:
        RoleNotFoundException: Si le rôle n'existe pas
    """
    try:
        role_obj = Role.objects.get(slug=role)
    except Role.DoesNotExist:
        raise RoleNotFoundException(detail=f"Le rôle '{role}' n'existe pas")
    
    # Filtrer les RoleGrants selon le groupe si fourni
    if user_group:
        # Si assigné via un groupe, utiliser les RoleGrants spécifiques au groupe ou génériques
        role_grants = RoleGrant.objects.filter(
            role__slug=role
        ).filter(
            Q(group=user_group.group) | Q(group__isnull=True)
        )
    else:
        # Si assigné directement, utiliser uniquement les RoleGrants génériques
        role_grants = RoleGrant.objects.filter(role__slug=role, group__isnull=True)

    for rg in role_grants:
        Grant.objects.update_or_create(
            user=user,
            scope=rg.scope,
            role=role_obj,
            defaults={
                "actions": expand_actions(rg.actions),
                "context": rg.context,
                "user_group": user_group,
                "created_by": by,
            }
        )

def revoke_role(user: AbstractBaseUser, role: str) -> tuple[int, dict[str, int]]:
    """
    Révoque un rôle d'un utilisateur en supprimant tous les grants associés.
    
    Args:
        user: L'utilisateur dont on révoque le rôle
        role: Le slug du rôle à révoquer
        
    Returns:
        Tuple contenant le nombre d'objets supprimés et un dictionnaire des types supprimés
        
    Raises:
        RoleNotFoundException: Si le rôle n'existe pas
    """
    try:
        role_obj = Role.objects.get(slug=role)
    except Role.DoesNotExist:
        raise RoleNotFoundException(detail=f"Le rôle '{role}' n'existe pas")
    
    return Grant.objects.filter(
        user__pk=user.pk,
        role__slug=role
    ).delete()


@transaction.atomic
def assign_group(user: AbstractBaseUser, group: str, by: Optional[AbstractBaseUser] = None) -> UserGroup:
    """
    Assigne tous les rôles d'un groupe à un utilisateur.
    
    Args:
        user: L'utilisateur à qui assigner le groupe
        group: Le slug du groupe à assigner
        by: L'utilisateur qui effectue l'assignation (pour traçabilité)
        
    Returns:
        L'objet UserGroup créé ou existant
        
    Raises:
        GroupNotFoundException: Si le groupe n'existe pas
        GroupAlreadyAssignedException: Si le groupe est déjà assigné
    """
    if UserGroup.objects.filter(user=user, group__slug=group).exists():
        raise GroupAlreadyAssignedException(
            detail=f"Le groupe '{group}' est déjà assigné à l'utilisateur"
        )
    
    try:
        _group: Group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise GroupNotFoundException(detail=f"Le groupe '{group}' n'existe pas")
    
    # Créer le UserGroup d'abord
    user_group, created = UserGroup.objects.get_or_create(user=user, group=_group)

    # Assigner tous les rôles du groupe avec le lien vers UserGroup
    for role in _group.roles.all():
        assign_role(user, role.slug, by=by, user_group=user_group)
    
    return user_group


@transaction.atomic
def revoke_group(user: AbstractBaseUser, group: str) -> tuple[int, dict[str, int]]:
    """
    Révoque tous les rôles d'un groupe d'un utilisateur.
    Supprime tous les grants liés au UserGroup et le UserGroup lui-même.
    
    Args:
        user: L'utilisateur dont on révoque le groupe
        group: Le slug du groupe à révoquer
        
    Returns:
        Tuple contenant le nombre d'objets supprimés et un dictionnaire des types supprimés
        
    Raises:
        GroupNotFoundException: Si le groupe n'existe pas
        GroupNotFoundException: Si le groupe n'est pas assigné à l'utilisateur
    """
    try:
        _group: Group = Group.objects.get(slug=group)
    except Group.DoesNotExist:
        raise GroupNotFoundException(detail=f"Le groupe '{group}' n'existe pas")
    
    try:
        user_group = UserGroup.objects.get(user=user, group=_group)
    except UserGroup.DoesNotExist:
        raise GroupNotFoundException(
            detail=f"Le groupe '{group}' n'est pas assigné à l'utilisateur"
        )
    
    # Supprimer tous les grants liés à ce UserGroup
    grants_deleted, grants_info = Grant.objects.filter(
        user=user,
        user_group=user_group
    ).delete()
    
    # Supprimer le UserGroup
    user_group.delete()
    
    return grants_deleted, grants_info


@transaction.atomic
def override_grant(
    user: AbstractBaseUser,
    scope: str,
    remove_actions: list[str]
) -> None:
    """
    Modifie un grant existant en retirant certaines actions.
    Si toutes les actions sont retirées, le grant est supprimé.
    Le grant devient personnalisé (role=None) après modification.
    
    Args:
        user: L'utilisateur dont on modifie le grant
        scope: Le scope du grant à modifier
        remove_actions: Liste des actions à retirer (seront expandées)
        
    Raises:
        GrantNotFoundException: Si le grant n'existe pas
    """
    grant: Optional[Grant] = Grant.objects.select_related("user_group", "role").filter(user__pk=user.pk, scope=scope).first()
    if not grant:
        raise GrantNotFoundException(
            detail=f"Aucun grant trouvé pour l'utilisateur sur le scope '{scope}'"
        )

    # Travailler avec les actions expandées du grant
    current_actions: set[str] = set(grant.actions)
    # Ne PAS expander les actions à retirer - on retire seulement ce qui est demandé
    actions_to_remove: set[str] = set(remove_actions)

    # Retirer les actions demandées des actions actuelles
    remaining_actions = current_actions - actions_to_remove

    # Si plus d'actions, supprimer le grant
    if not remaining_actions:
        user_group = grant.user_group
        grant.delete()
        
        # Si le grant était lié à un UserGroup, vérifier s'il reste des grants pour ce groupe
        if user_group:
            remaining_grants = Grant.objects.filter(
                user=user,
                user_group=user_group
            ).exists()
            
            # Si plus aucun grant lié à ce UserGroup, supprimer le UserGroup
            if not remaining_grants:
                user_group.delete()
        
        return

    # Mettre à jour le grant avec les nouvelles actions (garder la forme expandée)
    grant.actions = sorted(remaining_actions)
    grant.role = None  # Le grant devient personnalisé
    grant.save(update_fields=["actions", "role", "updated_at"])


@transaction.atomic
def group_sync(group_slug: str) -> dict[str, int]:
    """
    Synchronise les grants de tous les utilisateurs d'un groupe après modification des RoleGrants.
    Réapplique tous les rôles du groupe pour assurer la cohérence des permissions héritées.
    
    Cette fonction doit être appelée après :
    - Création/modification/suppression d'un RoleGrant lié à un groupe
    - Ajout/suppression d'un rôle dans un groupe
    
    Args:
        group_slug: Le slug du groupe à synchroniser
        
    Returns:
        Dictionnaire avec les statistiques:
        {
            "users_synced": nombre d'utilisateurs synchronisés,
            "grants_updated": nombre de grants mis à jour/créés
        }
        
    Raises:
        GroupNotFoundException: Si le groupe n'existe pas
        
    Example:
        >>> # Après modification d'un RoleGrant
        >>> group_sync("admins")
        {"users_synced": 5, "grants_updated": 15}
    """
    try:
        group = Group.objects.prefetch_related('roles').get(slug=group_slug)
    except Group.DoesNotExist:
        raise GroupNotFoundException(detail=f"Le groupe '{group_slug}' n'existe pas")
    
    # Récupérer tous les UserGroups liés à ce groupe
    user_groups = UserGroup.objects.filter(group=group).select_related('user')
    
    stats = {
        "users_synced": 0,
        "grants_updated": 0
    }
    
    # Pour chaque utilisateur du groupe
    for user_group in user_groups:
        user = user_group.user
        
        # Récupérer les scopes avec des grants personnalisés (role=None) pour cet utilisateur et ce UserGroup
        # Ces scopes doivent être exclus de la synchronisation
        overridden_scopes = set(
            Grant.objects.filter(
                user=user,
                user_group=user_group,
                role__isnull=True
            ).values_list('scope', flat=True)
        )
        
        # Supprimer uniquement les grants liés à ce UserGroup qui ont un rôle
        # Les grants avec role=None sont des grants personnalisés (overridés) et doivent être préservés
        deleted_count, _ = Grant.objects.filter(
            user=user,
            user_group=user_group,
            role__isnull=False  # Ne supprimer que les grants avec un rôle
        ).delete()
        
        # Préparer les grants à créer en bulk
        grants_to_create = []
        
        # Réassigner tous les rôles du groupe
        for role in group.roles.all():
            # Récupérer les RoleGrants pour ce rôle (spécifiques au groupe + génériques)
            role_grants = RoleGrant.objects.filter(
                role=role
            ).filter(
                Q(group=group) | Q(group__isnull=True)
            )
            
            # Préparer les grants correspondants, en excluant les scopes overridés
            for rg in role_grants:
                # Ignorer ce scope s'il a un grant personnalisé
                if rg.scope in overridden_scopes:
                    continue
                
                grants_to_create.append(
                    Grant(
                        user=user,
                        scope=rg.scope,
                        role=role,
                        actions=expand_actions(rg.actions),
                        context=rg.context,
                        user_group=user_group,
                    )
                )
        
        # Créer tous les grants en une seule requête
        if grants_to_create:
            Grant.objects.bulk_create(
                grants_to_create,
                update_conflicts=True,
                unique_fields=["user", "scope", "role", "user_group"],
                update_fields=["actions", "context", "updated_at"]
            )
            stats["grants_updated"] += len(grants_to_create)
        
        stats["users_synced"] += 1
    
    return stats


def check(
    user: AbstractBaseUser,
    scope: str,
    required: list[str],
    role: Optional[str] = None,
    **context: Any
) -> bool:
    """
    Vérifie si un utilisateur possède les permissions requises pour un scope donné.
    Utilise l'opérateur PostgreSQL @> (contains) pour vérifier que toutes les actions
    requises sont présentes dans le grant.
    
    Args:
        user: L'utilisateur dont on vérifie les permissions
        scope: Le scope à vérifier (ex: 'articles', 'users', 'comments')
        required: Liste des actions requises (ex: ['r'], ['w', 'r'], ['d'])
        role: Slug du rôle optionnel pour filtrer les grants par rôle.
              Si None, vérifie globalement tous les grants du scope.
        **context: Contexte additionnel pour filtrer les grants (clés JSON)
        
    Returns:
        True si l'utilisateur possède toutes les actions requises, False sinon
        
    Example:
        >>> # Vérification globale : l'utilisateur peut-il lire les articles ?
        >>> check(user, 'articles', ['r'])
        True
        >>> # Vérification par rôle : a-t-il ce droit via le rôle 'admin' ?
        >>> check(user, 'articles', ['w'], role='admin')
        True
        >>> # Vérifier avec contexte
        >>> check(user, 'articles', ['w'], tenant_id=123)
        False
        
    Note:
        Les actions sont automatiquement expandées lors de la création du grant,
        donc vérifier ['w'] vérifiera aussi ['r'] implicitement.
    """
    # Construire le filtre de base
    grant_filter = Q(
        user__pk=user.pk,
        scope=scope,
        actions__contains=list(required),
    )
    
    # Filtrer par rôle si spécifié
    if role:
        grant_filter &= Q(role__slug=role)
    
    # Ajouter les filtres de contexte si fournis
    if context:
        grant_filter &= Q(context__contains=context)
    
    # Vérifier l'existence d'un grant correspondant
    return Grant.objects.filter(grant_filter).exists()


def any_action_check(
    user: AbstractBaseUser,
    scope: str,
    required: list[str],
    role: Optional[str] = None,
    **context: Any
) -> bool:
    """
    Vérifie si un utilisateur possède au moins une des actions requises pour un scope donné.
    
    Cette fonction utilise une seule requête optimisée avec des conditions OR pour vérifier
    si l'utilisateur possède au moins une des actions dans la liste.
    
    Args:
        user: L'utilisateur dont on vérifie les permissions
        scope: Le scope à vérifier (ex: 'articles', 'invoices')
        required: Liste des actions dont au moins une est requise (ex: ['r', 'w'], ['d'])
        role: Slug du rôle optionnel pour filtrer les grants par rôle.
              Si None, vérifie globalement tous les grants du scope.
        **context: Contexte additionnel pour filtrer les grants (clés JSON)
        
    Returns:
        True si l'utilisateur possède au moins une des actions requises, False sinon
        
    Example:
        >>> # Vérification globale
        >>> any_action_check(user, 'articles', ['r', 'w'])
        True
        >>> # Vérification par rôle
        >>> any_action_check(user, 'articles', ['r', 'w'], role='editor')
        True
        >>> # Vérifier avec contexte
        >>> any_action_check(user, 'articles', ['w', 'd'], tenant_id=123)
        False
        
    Note:
        Les actions sont automatiquement expandées lors de la création du grant,
        donc si un grant contient ['w'], il contient aussi ['r'] implicitement.
        Cette fonction vérifie si AU MOINS UNE des actions requises est présente.
    """
    # Construire le filtre de base pour l'utilisateur et le scope
    grant_filter = Q(user__pk=user.pk, scope=scope)
    
    # Filtrer par rôle si spécifié
    if role:
        grant_filter &= Q(role__slug=role)
    
    # Ajouter les filtres de contexte si fournis
    if context:
        grant_filter &= Q(context__contains=context)
    
    # Vérifier si au moins une des actions requises est présente dans le grant
    # Utilise l'opérateur overlap (&&) pour une requête optimale
    grant_filter &= Q(actions__overlap=required)
    
    # Vérifier l'existence d'un grant correspondant
    return Grant.objects.filter(grant_filter).exists()


def any_permission_check(user: AbstractBaseUser, *str_perms: str) -> bool:
    """
    Vérifie si un utilisateur possède au moins une des permissions fournies.
    
    Cette fonction parse toutes les permissions fournies et effectue une seule requête
    optimisée avec des conditions OR pour vérifier si l'utilisateur possède au moins
    une des permissions.
    
    Args:
        user: L'utilisateur dont on vérifie les permissions
        *str_perms: Liste de chaînes de permissions au format standard
                    (ex: 'articles:r', 'invoices:w:admin', 'users:d?tenant_id=123')
        
    Returns:
        True si l'utilisateur possède au moins une des permissions, False sinon
        
    Example:
        >>> # Vérification globale
        >>> any_permission_check(user, 'articles:r', 'invoices:w')
        True
        >>> # Avec différents rôles et contextes
        >>> any_permission_check(
        ...     user,
        ...     'articles:w:editor',
        ...     'invoices:r:accountant',
        ...     'users:d?tenant_id=123'
        ... )
        False
        
    Note:
        Toute la vérification se fait au niveau de la base de données avec une seule
        requête utilisant des conditions OR pour optimiser les performances.
    """
    if not str_perms:
        return False
    
    # Construire le filtre de base pour l'utilisateur
    base_filter = Q(user__pk=user.pk)
    
    # Construire les conditions OR pour chaque permission
    permission_filters = Q()
    
    for perm in str_perms:
        # Parser la permission
        scope, actions, role, context = parse_permission(perm)
        
        # Construire le filtre pour cette permission spécifique
        perm_filter = Q(scope=scope, actions__overlap=actions)
        
        # Filtrer par rôle si spécifié
        if role:
            perm_filter &= Q(role__slug=role)
        
        # Ajouter le filtre de contexte si fourni
        if context:
            perm_filter &= Q(context__contains=context)
        
        # Ajouter cette permission aux conditions OR
        permission_filters |= perm_filter
    
    # Combiner le filtre de base avec les conditions OR et vérifier l'existence
    return Grant.objects.filter(base_filter & permission_filters).exists()


def parse_permission(perm: str) -> tuple[str, list[str], Optional[str], dict[str, Any]]:
    """
    Parse une chaîne de permission et retourne ses composants.
    
    Formats supportés:
        - "<scope>:<actions>" : vérification globale sur le scope
        - "<scope>:<actions>:<role>" : vérification liée à un rôle spécifique
        - "<scope>:<actions>?key=value" : vérification globale avec contexte
        - "<scope>:<actions>:<role>?key=value" : vérification par rôle avec contexte
    
    Args:
        perm: Chaîne de permission au format "<scope>:<actions>:<role>?key=value&key2=value2"
              - scope: Le scope (ex: 'articles')
              - actions: Actions requises (ex: 'rw', 'r', 'rwdx')
              - role: (Optionnel) Slug du rôle pour filtrer
              - query params: (Optionnel) Contexte sous forme de query parameters
              
    Returns:
        Tuple contenant (scope, actions_list, role, context_dict)
        
    Raises:
        ValueError: Si le format de la permission est invalide
        
    Example:
        >>> parse_permission('articles:rw')
        ('articles', ['r', 'w'], None, {})
        >>> parse_permission('articles:w:admin')
        ('articles', ['w'], 'admin', {})
        >>> parse_permission('articles:rw?tenant_id=123&status=published')
        ('articles', ['r', 'w'], None, {'tenant_id': 123, 'status': 'published'})
        >>> parse_permission('articles:w:editor?tenant_id=123')
        ('articles', ['w'], 'editor', {'tenant_id': 123})
    """
    # Séparer la partie principale des query params
    if '?' in perm:
        from urllib.parse import parse_qs

        main_part, query_string = perm.split('?', 1)
        # Parser les query params
        parsed_qs = parse_qs(query_string)
        # Convertir en dict simple (prendre la première valeur de chaque liste)
        query_context = {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}
        # Convertir les valeurs numériques
        for k, v in query_context.items():
            if isinstance(v, str) and v.isdigit():
                query_context[k] = int(v)
    else:
        main_part = perm
        query_context = {}
    
    # Parser la partie principale
    parts = main_part.split(':')
    
    if len(parts) < 2:
        raise ValueError(
            f"Format de permission invalide: '{perm}'. "
            "Format attendu: '<scope>:<actions>' ou '<scope>:<actions>:<role>' "
            "ou '<scope>:<actions>:<role>?key=value&key2=value2'"
        )
    
    scope = parts[0]
    actions_str = parts[1]
    role = parts[2] if len(parts) > 2 else None
    
    # Convertir la chaîne d'actions en liste
    # 'rwd' -> ['r', 'w', 'd']
    actions_list = list(actions_str)
    
    return scope, actions_list, role, query_context


def str_check(user: AbstractBaseUser, perm: str, **context: Any) -> bool:
    """
    Vérifie si un utilisateur possède les permissions requises à partir d'une chaîne formatée.
    
    Args:
        user: L'utilisateur dont on vérifie les permissions
        perm: Chaîne de permission au format "<scope>:<actions>:<role>?key=value&key2=value2"
              - scope: Le scope à vérifier (ex: 'articles')
              - actions: Actions requises (ex: 'rw', 'r', 'rwdx')
              - role: (Optionnel) Slug du rôle pour filtrer
              - query params: (Optionnel) Contexte sous forme de query parameters
        **context: Contexte additionnel pour filtrer les grants (fusionné avec les query params)
        
    Returns:
        True si l'utilisateur possède les permissions requises, False sinon
        
    Example:
        >>> # Vérification globale
        >>> str_check(user, 'articles:r')
        True
        >>> # Vérification par rôle
        >>> str_check(user, 'articles:w:admin')
        True
        >>> # Avec contexte via query params
        >>> str_check(user, 'articles:w?tenant_id=123&status=published')
        False
        >>> # Avec rôle et contexte
        >>> str_check(user, 'articles:w:editor?tenant_id=123')
        True
        >>> # Contexte mixte (query params + kwargs)
        >>> str_check(user, 'articles:w?tenant_id=123', level=2)
        False
    """
    from .caches import cache_check

    # Parser la chaîne de permission
    scope, required, role, query_context = parse_permission(perm)
    
    # Fusionner les contextes (kwargs ont priorité sur query params)
    final_context = {**query_context, **context}
    
    return cache_check(user, scope, required, role=role, **final_context)

def load_preset(*, force: bool = False) -> dict[str, int]:
    """
    Charge un preset de permissions depuis les settings Django.
    Utilisé par la commande de management load_permission_preset.
    
    Par sécurité, si des rôles existent déjà en base, la fonction lève une exception
    sauf si force=True est passé explicitement.
    
    Args:
        force: Si True, permet de charger le preset même si des rôles existent déjà.
               Par défaut False pour éviter l'écrasement accidentel.
    
    Le preset doit être défini dans settings.PERMISSION_PRESET avec la structure suivante:
    
    PERMISSION_PRESET = {
        "roles": [
            {
                "name": "Accountant",
                "slug": "accountant"
            },
            {
                "name": "Admin",
                "slug": "admin"
            }
        ],
        "scopes": ['users', 'articles', 'comments'],
        "group": [
            {
                "name": "Admins",
                "slug": "admins",
                "app": "my_app",
                "roles": ["admin"]
            },
            {
                "name": "Accountants",
                "slug": "accountants",
                "roles": ["accountant"]
            }
        ],
        "role_grants": [
            {
                "role": "admin",
                "scope": "users",
                "actions": ["r", "w", "d"],
                "context": {}
                # "group": "slug"  # Optionnel: si absent ou None, RoleGrant générique
            },
            {
                "role": "accountant",
                "scope": "users",
                "actions": ["r"],
                "context": {},
                "group": "accountants"  # RoleGrant spécifique au groupe accountants
            }
        ]
    }
    
    Returns:
        Dictionnaire avec les statistiques de création:
        {
            "roles": nombre de rôles créés,
            "groups": nombre de groupes créés,
            "role_grants": nombre de role_grants créés
        }
        
    Raises:
        AttributeError: Si PERMISSION_PRESET n'est pas défini dans settings
        KeyError: Si une clé requise est manquante dans le preset
        PermissionError: Si des rôles existent déjà et force=False
    """
    from django.conf import settings
    
    # Récupérer le preset depuis les settings
    preset = getattr(settings, 'PERMISSION_PRESET', None)
    if preset is None:
        raise AttributeError(
            "PERMISSION_PRESET n'est pas défini dans les settings Django"
        )
    
    # Sécurité : vérifier si des rôles existent déjà
    existing_roles_count = Role.objects.count()
    if existing_roles_count > 0 and not force:
        raise PermissionError(
            f"Des rôles existent déjà en base de données ({existing_roles_count} rôle(s)). "
            "Pour charger le preset malgré tout, utilisez l'option --force. "
            "Attention : cela peut créer des doublons ou modifier les permissions existantes."
        )
    
    stats = {
        "roles": 0,
        "groups": 0,
        "role_grants": 0
    }
    
    # Cache local pour éviter les requêtes répétées
    roles_cache: dict[str, Role] = {}
    groups_cache: dict[str, Group] = {}
    
    # Créer les rôles et peupler le cache
    roles_data = preset.get('roles', [])
    for role_data in roles_data:
        defaults = {'name': role_data['name']}
        # App field is optional
        if 'app' in role_data:
            defaults['app'] = role_data['app']
            
        role, created = Role.objects.get_or_create(
            slug=role_data['slug'],
            defaults=defaults
        )
        roles_cache[role.slug] = role
        if created:
            stats['roles'] += 1
    
    # Créer les groupes et peupler le cache
    groups_data = preset.get('group', [])
    for group_data in groups_data:
        defaults = {'name': group_data['name']}
        # App field is optional
        if 'app' in group_data:
            defaults['app'] = group_data['app']
        group, created = Group.objects.get_or_create(
            slug=group_data['slug'],
            defaults=defaults
        )
        groups_cache[group.slug] = group
        if created:
            stats['groups'] += 1
        
        # Associer les rôles au groupe en utilisant le cache
        role_slugs = group_data.get('roles', [])
        for role_slug in role_slugs:
            # Utiliser le cache au lieu de requêter la base
            role = roles_cache.get(role_slug)
            if role is None:
                raise ValueError(
                    f"Le rôle '{role_slug}' n'existe pas pour le groupe '{group.slug}'"
                )
            group.roles.add(role)
    
    # Créer les role_grants en utilisant le cache
    role_grants_data = preset.get('role_grants', [])
    for rg_data in role_grants_data:
        # Utiliser le cache au lieu de requêter la base
        role = roles_cache.get(rg_data['role'])
        if role is None:
            raise ValueError(
                f"Le rôle '{rg_data['role']}' n'existe pas pour le role_grant"
            )
        
        # Gérer le groupe optionnel
        group_obj = None
        group_slug = rg_data.get('group')
        if group_slug:
            group_obj = groups_cache.get(group_slug)
            if group_obj is None:
                raise ValueError(
                    f"Le groupe '{group_slug}' n'existe pas pour le role_grant"
                )
        
        # Utiliser get_or_create avec la contrainte complète (role, scope, group)
        role_grant, created = RoleGrant.objects.get_or_create(
            role=role,
            scope=rg_data['scope'],
            group=group_obj,
            defaults={
                'actions': rg_data.get('actions', []),
                'context': rg_data.get('context', {})
            }
        )
        if created:
            stats['role_grants'] += 1
    
    return stats
