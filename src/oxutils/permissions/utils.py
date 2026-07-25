from typing import Any, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import Q

from .actions import expand_actions
from .exceptions import (
    GrantNotFoundException,
    GroupAlreadyAssignedException,
    GroupNotFoundException,
    RoleNotFoundException,
)
from .models import Grant, Group, Role, RoleGrant, UserGroup


@transaction.atomic
def assign_role(
    user: AbstractBaseUser,
    role: str,
    scope: str,
    *,
    by: Optional[AbstractBaseUser] = None,
    user_group: Optional[UserGroup] = None,
) -> None:
    """
    Assigne un rôle à un utilisateur en créant ou mettant à jour les grants correspondants.

    Args:
        user: L'utilisateur à qui assigner le rôle
        role: Le slug du rôle à assigner
        scope: Le scope pour lequel assigner le rôle
        by: L'utilisateur qui effectue l'assignation (pour traçabilité)
        user_group: Le UserGroup associé si le rôle est assigné via un groupe

    Raises:
        RoleNotFoundException: Si le rôle n'existe pas
    """
    try:
        role_obj = Role.objects.get(slug=role)
    except Role.DoesNotExist as exc:
        raise RoleNotFoundException(detail=f"Le rôle '{role}' n'existe pas") from exc

    # Récupérer tous les RoleGrants pour ce rôle
    role_grants = RoleGrant.objects.filter(role__slug=role, scope=scope)

    for rg in role_grants:
        Grant.objects.update_or_create(
            user=user,
            scope=rg.scope,
            role=role_obj,
            defaults={
                "actions": expand_actions(rg.scope, rg.actions),
                "context": rg.context,
                "user_group": user_group,
                "created_by": by,
            },
        )


def revoke_role(user: AbstractBaseUser, role: str, scope: str) -> tuple[int, dict[str, int]]:
    """
    Révoque un rôle d'un utilisateur en supprimant tous les grants associés pour un scope donné.

    Args:
        user: L'utilisateur dont on révoque le rôle
        role: Le slug du rôle à révoquer
        scope: Le scope pour lequel révoquer le rôle

    Returns:
        Tuple contenant le nombre d'objets supprimés et un dictionnaire des types supprimés

    Raises:
        RoleNotFoundException: Si le rôle n'existe pas
    """
    try:
        role_obj = Role.objects.get(slug=role)
    except Role.DoesNotExist as exc:
        raise RoleNotFoundException(detail=f"Le rôle '{role}' n'existe pas") from exc

    return Grant.objects.filter(user__pk=user.pk, role__slug=role, scope=scope).delete()


@transaction.atomic
def assign_group(
    user: AbstractBaseUser, group: str, by: Optional[AbstractBaseUser] = None
) -> UserGroup:
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
    except Group.DoesNotExist as exc:
        raise GroupNotFoundException(detail=f"Le groupe '{group}' n'existe pas") from exc

    # Créer le UserGroup d'abord
    user_group, created = UserGroup.objects.get_or_create(user=user, group=_group)

    # Assigner tous les rôles du groupe avec le lien vers UserGroup
    for role in _group.roles.all():
        # Récupérer tous les scopes pour ce rôle
        scopes = RoleGrant.objects.filter(role=role).values_list("scope", flat=True).distinct()
        for scope in scopes:
            assign_role(user, role.slug, scope, by=by, user_group=user_group)

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
    except Group.DoesNotExist as exc:
        raise GroupNotFoundException(detail=f"Le groupe '{group}' n'existe pas") from exc

    try:
        user_group = UserGroup.objects.get(user=user, group=_group)
    except UserGroup.DoesNotExist as exc:
        raise GroupNotFoundException(
            detail=f"Le groupe '{group}' n'est pas assigné à l'utilisateur"
        ) from exc

    # Supprimer tous les grants liés à ce UserGroup
    grants_deleted, grants_info = Grant.objects.filter(user=user, user_group=user_group).delete()

    # Supprimer le UserGroup
    user_group.delete()

    return grants_deleted, grants_info


@transaction.atomic
def override_grant(
    user: AbstractBaseUser, scope: str, actions: list[str], role: Optional[str] = None
) -> None:
    """
    Modifie un grant existant en définissant de nouvelles actions.
    Si actions est vide, le grant est supprimé.
    Le grant devient verrouillé (locked=True) après modification.

    Args:
        user: L'utilisateur dont on modifie le grant
        scope: Le scope du grant à modifier
        actions: Liste des nouvelles actions (seront expandées). Si vide, supprime le grant.
        role: Optionnel, slug du rôle pour filtrer le grant spécifique

    Raises:
        GrantNotFoundException: Si le grant n'existe pas
    """
    queryset = Grant.objects.select_related("user_group", "role").filter(
        user__pk=user.pk, scope=scope
    )

    if role:
        queryset = queryset.filter(role__slug=role)

    grant: Optional[Grant] = queryset.first()
    if not grant:
        raise GrantNotFoundException(
            detail=f"Aucun grant trouvé pour l'utilisateur sur le scope '{scope}'"
        )

    # Si actions est vide, supprimer le grant
    if not actions:
        user_group = grant.user_group
        grant.delete()

        # Si le grant était lié à un UserGroup, vérifier s'il reste des grants pour ce groupe
        if user_group:
            remaining_grants = Grant.objects.filter(user=user, user_group=user_group).exists()

            # Si plus aucun grant lié à ce UserGroup, supprimer le UserGroup
            if not remaining_grants:
                user_group.delete()

        return

    # Expander et définir les nouvelles actions
    expanded_actions = expand_actions(scope, actions)
    grant.actions = expanded_actions
    grant.locked = True  # Le grant devient verrouillé (protégé du group_sync)
    grant.save(update_fields=["actions", "locked", "updated_at"])


@transaction.atomic
def group_sync(
    group_slug: str, role_slugs: Optional[list[str]] = None, scope: Optional[str] = None
) -> dict[str, int]:
    """
    Synchronise les grants de tous les utilisateurs d'un groupe après modification des RoleGrants.
    Réapplique tous les rôles du groupe pour assurer la cohérence des permissions héritées.

    Cette fonction doit être appelée après :
    - Création/modification/suppression d'un RoleGrant
    - Ajout/suppression d'un rôle dans un groupe

    Args:
        group_slug: Le slug du groupe à synchroniser
        role_slugs: Optionnel, liste des slugs de rôles pour limiter la synchronisation à ces rôles uniquement
        scope: Optionnel, scope spécifique pour limiter la synchronisation (améliore les performances)

    Returns:
        Dictionnaire avec les statistiques:
        {
            "users_synced": nombre d'utilisateurs synchronisés,
            "grants_updated": nombre de grants mis à jour/créés
        }

    Raises:
        GroupNotFoundException: Si le groupe n'existe pas
        RoleNotFoundException: Si un des rôles spécifiés n'existe pas

    Example:
        >>> # Après modification d'un RoleGrant
        >>> group_sync("admins")
        {"users_synced": 5, "grants_updated": 15}

        >>> # Synchroniser uniquement le rôle 'editor'
        >>> group_sync("admins", role_slugs=["editor"])
        {"users_synced": 5, "grants_updated": 5}

        >>> # Synchroniser plusieurs rôles pour un scope spécifique
        >>> group_sync("admins", role_slugs=["editor", "viewer"], scope="articles")
        {"users_synced": 5, "grants_updated": 3}
    """
    try:
        group = Group.objects.prefetch_related("roles").get(slug=group_slug)
    except Group.DoesNotExist as exc:
        raise GroupNotFoundException(detail=f"Le groupe '{group_slug}' n'existe pas") from exc

    # Si des rôles spécifiques sont demandés, vérifier qu'ils existent et appartiennent au groupe
    if role_slugs:
        group_role_slugs = set(group.roles.values_list("slug", flat=True))
        for role_slug in role_slugs:
            try:
                Role.objects.get(slug=role_slug)
                if role_slug not in group_role_slugs:
                    raise RoleNotFoundException(
                        detail=f"Le rôle '{role_slug}' n'appartient pas au groupe '{group_slug}'"
                    )
            except Role.DoesNotExist as exc:
                raise RoleNotFoundException(detail=f"Le rôle '{role_slug}' n'existe pas") from exc

    # Construire une subquery pour identifier les grants verrouillés
    # Ces grants doivent être exclus de la synchronisation
    locked_grants_subquery = Grant.objects.filter(user_group__group=group, locked=True)

    # Appliquer les mêmes filtres que pour la synchronisation
    if scope:
        locked_grants_subquery = locked_grants_subquery.filter(scope=scope)
    if role_slugs:
        locked_grants_subquery = locked_grants_subquery.filter(role__slug__in=role_slugs)

    # Supprimer uniquement les grants liés à ce groupe qui ne sont pas verrouillés
    # Les grants avec locked=True sont des grants personnalisés (overridés) et doivent être préservés
    delete_query = Grant.objects.filter(
        user_group__group=group,
        locked=False,  # Ne supprimer que les grants non verrouillés
    )

    # Si des rôles spécifiques sont demandés, ne supprimer que les grants de ces rôles
    if role_slugs:
        delete_query = delete_query.filter(role__slug__in=role_slugs)

    # Si un scope spécifique est demandé, ne supprimer que les grants de ce scope
    if scope:
        delete_query = delete_query.filter(scope=scope)

    deleted_count, _ = delete_query.delete()

    # Préparer les grants à créer en bulk
    grants_to_create = []

    # Réassigner tous les rôles du groupe (ou uniquement les rôles spécifiés)
    roles_to_sync = group.roles.filter(slug__in=role_slugs) if role_slugs else group.roles.all()

    # Récupérer tous les RoleGrants pour tous les rôles en une seule requête
    role_grants_query = RoleGrant.objects.filter(role__in=roles_to_sync)

    # Si un scope spécifique est demandé, filtrer uniquement ce scope
    if scope:
        role_grants_query = role_grants_query.filter(scope=scope)

    # Récupérer tous les UserGroups pour ce groupe
    user_groups = UserGroup.objects.filter(group=group).select_related("user")

    # Préparer les grants correspondants, en excluant les grants verrouillés via subquery
    for user_group in user_groups:
        for rg in role_grants_query:
            grants_to_create.append(
                Grant(
                    user=user_group.user,
                    scope=rg.scope,
                    role=rg.role,
                    actions=expand_actions(rg.scope, rg.actions),
                    context=rg.context,
                    user_group=user_group,
                )
            )

    # Créer tous les grants en une seule requête, en excluant ceux qui sont verrouillés
    # On utilise ignore_conflicts au lieu de update_conflicts pour éviter d'écraser les grants verrouillés
    if grants_to_create:
        # Filtrer les grants à créer pour exclure ceux qui correspondent à des grants verrouillés
        # On compare (user_id, scope, role_id) avec la subquery
        locked_grant_ids = locked_grants_subquery.values_list("user_id", "scope", "role_id")
        locked_set = set(locked_grant_ids)

        # Filtrer les grants à créer
        filtered_grants = [
            grant
            for grant in grants_to_create
            if (grant.user.id, grant.scope, grant.role.pk) not in locked_set
        ]

        if filtered_grants:
            Grant.objects.bulk_create(
                filtered_grants,
                ignore_conflicts=True,
            )

    # Compter le nombre d'utilisateurs synchronisés
    users_synced = user_groups.count()

    return {"users_synced": users_synced, "grants_updated": len(grants_to_create)}


@transaction.atomic
def role_sync(role_slug: str, scope: Optional[str] = None) -> dict[str, int]:
    """
    Synchronise les grants pour un rôle spécifique après modification des RoleGrants.
    Met à jour directement les permissions du rôle pour tous les utilisateurs qui ont ce rôle de manière indépendante (non lié à un groupe).

    Cette fonction doit être appelée après :
    - Création/modification/suppression d'un RoleGrant pour ce rôle

    Args:
        role_slug: Le slug du rôle à synchroniser
        scope: Optionnel, scope spécifique pour limiter la synchronisation (améliore les performances)

    Returns:
        Dictionnaire avec les statistiques:
        {
            "grants_updated": nombre de grants mis à jour
        }

    Raises:
        RoleNotFoundException: Si le rôle n'existe pas

    Example:
        >>> # Après modification d'un RoleGrant
        >>> role_sync("editor")
        {"grants_updated": 12}

        >>> # Synchroniser uniquement pour un scope spécifique
        >>> role_sync("editor", scope="articles")
        {"grants_updated": 3}
    """
    try:
        role = Role.objects.get(slug=role_slug)
    except Role.DoesNotExist as exc:
        raise RoleNotFoundException(detail=f"Le rôle '{role_slug}' n'existe pas") from exc

    # Récupérer tous les RoleGrants pour ce rôle
    role_grants_query = RoleGrant.objects.filter(role=role)

    # Si un scope spécifique est demandé, filtrer uniquement ce scope
    if scope:
        role_grants_query = role_grants_query.filter(scope=scope)

    # Récupérer tous les grants non verrouillés pour ce rôle (indépendants)
    grants_query = Grant.objects.filter(role=role, locked=False, user_group__isnull=True)

    # Si un scope spécifique est demandé, filtrer uniquement ce scope
    if scope:
        grants_query = grants_query.filter(scope=scope)

    # Créer un mapping scope -> RoleGrant pour accès rapide
    role_grants_map = {f"{rg.scope}_{rg.role_id}": rg for rg in role_grants_query}

    # Mettre à jour les grants existants
    updated_count = 0

    for grant in grants_query:
        # Récupérer le RoleGrant correspondant au scope
        role_grant = role_grants_map.get(f"{grant.scope}_{grant.role_id}")

        if role_grant:
            # Mettre à jour les actions et le contexte directement
            grant.actions = expand_actions(role_grant.scope, role_grant.actions)
            grant.context = role_grant.context
            grant.save(update_fields=["actions", "context", "updated_at"])
            updated_count += 1

    return {"grants_updated": updated_count}


def check(
    user: AbstractBaseUser,
    scope: str,
    required: list[str],
    role: Optional[str] = None,
    **context: Any,
) -> bool:
    """
    Vérifie si un utilisateur possède **toutes** les actions requises pour un scope donné (AND).
    Utilise l'opérateur PostgreSQL @> (contains) pour vérifier que toutes les actions
    requises sont présentes dans le grant.

    Args:
        user: L'utilisateur dont on vérifie les permissions
        scope: Le scope à vérifier (ex: 'orders', 'articles')
        required: Liste des actions nommées requises (ex: ['create'], ['create', 'approve'])
        role: Slug du rôle optionnel pour filtrer les grants par rôle.
              Si None, vérifie globalement tous les grants du scope.
        **context: Contexte additionnel pour filtrer les grants (clés JSON)

    Returns:
        True si l'utilisateur possède toutes les actions requises, False sinon

    Example:
        >>> # Vérification globale : l'utilisateur peut-il créer des commandes ?
        >>> check(user, 'orders', ['create'])
        True
        >>> # Vérification AND : doit pouvoir créer ET approuver
        >>> check(user, 'orders', ['create', 'approve'])
        False
        >>> # Vérification par rôle
        >>> check(user, 'orders', ['create'], role='manager')
        True

    Note:
        Les actions sont automatiquement expandées lors de la création du grant,
        donc vérifier ['create'] fonctionne même si le grant stocke ['approve', 'create']
        (si 'approve' implique 'create' dans la hiérarchie).
    """
    # Construire le filtre de base
    grant_filter = Q(
        user__pk=user.pk,
        scope=scope,
        is_active=True,
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
    **context: Any,
) -> bool:
    """
    Vérifie si un utilisateur possède **au moins une** des actions requises pour un scope donné (OR).

    Cette fonction utilise une seule requête optimisée avec des conditions OR pour vérifier
    si l'utilisateur possède au moins une des actions dans la liste.

    Args:
        user: L'utilisateur dont on vérifie les permissions
        scope: Le scope à vérifier (ex: 'orders', 'articles')
        required: Liste des actions nommées dont au moins une est requise
                  (ex: ['create', 'approve'])
        role: Slug du rôle optionnel pour filtrer les grants par rôle.
              Si None, vérifie globalement tous les grants du scope.
        **context: Contexte additionnel pour filtrer les grants (clés JSON)

    Returns:
        True si l'utilisateur possède au moins une des actions requises, False sinon

    Example:
        >>> # Vérification OR globale
        >>> any_action_check(user, 'orders', ['create', 'approve'])
        True  # si l'utilisateur a create OU approve
        >>> # Vérification par rôle
        >>> any_action_check(user, 'orders', ['create', 'approve'], role='editor')
        True
    """
    # Construire le filtre de base pour l'utilisateur et le scope
    grant_filter = Q(user__pk=user.pk, scope=scope, is_active=True)

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


def activate_user_permissions(user: AbstractBaseUser, scope: Optional[str] = None, app: Optional[str] = None) -> None:
    """Active les permissions de l'utilisateur pour le scope et/ou l'application spécifiés.

    Passe ``is_active = True`` sur tous les *Grant* correspondants.
    Si aucun grant ne correspond, l'appel est sans effet (passif).
    """
    grants = Grant.objects.filter(user=user)
    if scope:
        grants = grants.filter(scope=scope)
    if app:
        grants = grants.filter(role__app=app)
    grants.update(is_active=True)


def deactivate_user_permissions(user: AbstractBaseUser, scope: Optional[str] = None, app: Optional[str] = None) -> None:
    """Désactive les permissions de l'utilisateur pour le scope et/ou l'application spécifiés.

    Passe ``is_active = False`` sur tous les *Grant* correspondants.
    Si aucun grant ne correspond, l'appel est sans effet (passif).
    """
    grants = Grant.objects.filter(user=user)
    if scope:
        grants = grants.filter(scope=scope)
    if app:
        grants = grants.filter(role__app=app)
    grants.update(is_active=False)


def any_permission_check(user: AbstractBaseUser, *str_perms: str) -> bool:
    """
    Vérifie si un utilisateur possède au moins une des permissions fournies.

    Cette fonction parse toutes les permissions fournies et effectue une seule requête
    optimisée avec des conditions OR pour vérifier si l'utilisateur possède au moins
    une des permissions.

    Chaque chaîne de permission peut utiliser :
        - ``/`` (AND) — toutes les actions sont requises
        - ``|`` (OR) — au moins une action est requise

    Args:
        user: L'utilisateur dont on vérifie les permissions
        *str_perms: Liste de chaînes de permissions au format
                    ``<scope>:<action1>/<action2>:<role>?key=value``
                    ou ``<scope>:<action1>|<action2>:<role>?key=value``

    Returns:
        True si l'utilisateur possède au moins une des permissions, False sinon

    Example:
        >>> # Vérification globale
        >>> any_permission_check(user, 'articles:read', 'invoices:write')
        True
        >>> # AND dans un scope, OR entre scopes
        >>> any_permission_check(
        ...     user,
        ...     'orders:create/approve',        # AND: doit avoir create ET approve
        ...     'articles:read|write:editor',   # OR: au moins read OU write via editor
        ... )
        False
    """
    if not str_perms:
        return False

    # Construire le filtre de base pour l'utilisateur
    base_filter = Q(user__pk=user.pk, is_active=True)

    # Construire les conditions OR pour chaque permission
    permission_filters = Q()

    for perm in str_perms:
        # Parser la permission (nouveau format avec opérateur)
        scope, actions, operator, role, context = parse_permission(perm)

        # Construire le filtre pour cette permission spécifique
        if operator == "|":
            # OR : au moins une action parmi la liste
            perm_filter = Q(scope=scope, actions__overlap=actions)
        else:
            # AND : toutes les actions doivent être présentes
            perm_filter = Q(scope=scope, actions__contains=actions)

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


def parse_permission(perm: str) -> tuple[str, list[str], str, Optional[str], dict[str, Any]]:
    """
    Parse une chaîne de permission et retourne ses composants.

    Formats supportés:
        - ``<scope>:<action>`` : action unique sur le scope
        - ``<scope>:<action1>/<action2>`` : AND — toutes les actions requises
        - ``<scope>:<action1>|<action2>`` : OR — au moins une action requise
        - ``<scope>:<action1>/<action2>:<role>`` : AND avec rôle
        - ``<scope>:<action1>|<action2>:<role>`` : OR avec rôle
        - ``<scope>:<action1>/<action2>:<role>?key=value`` : AND + rôle + contexte
        - ``<scope>:<action1>|<action2>:<role>?key=value`` : OR + rôle + contexte

    Args:
        perm: Chaîne de permission.

    Returns:
        Tuple ``(scope, actions_list, operator, role, context_dict)``

        - *scope*: le scope (ex: ``"orders"``)
        - *actions_list*: liste des actions nommées (ex: ``["create", "approve"]``)
        - *operator*: ``"&"`` (AND) ou ``"|"`` (OR)
        - *role*: slug du rôle ou ``None``
        - *context_dict*: dictionnaire de contexte extrait des query params

    Raises:
        ValueError: Si le format de la permission est invalide

    Example:
        >>> parse_permission('orders:create/approve')
        ('orders', ['create', 'approve'], '&', None, {})
        >>> parse_permission('orders:create|approve')
        ('orders', ['create', 'approve'], '|', None, {})
        >>> parse_permission('orders:create/approve:manager')
        ('orders', ['create', 'approve'], '&', 'manager', {})
        >>> parse_permission('articles:read?tenant_id=42')
        ('articles', ['read'], '&', None, {'tenant_id': 42})
    """
    # Séparer la partie principale des query params
    if "?" in perm:
        from urllib.parse import parse_qs

        main_part, query_string = perm.split("?", 1)
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
        query_context: dict[str, Any] = {}

    # Parser la partie principale : scope:actions[:role]
    parts = main_part.split(":")

    if len(parts) < 2:
        raise ValueError(
            f"Format de permission invalide: '{perm}'. "
            "Format attendu: '<scope>:<action>' ou '<scope>:<action1>/<action2>[:<role>]' "
            "ou '<scope>:<action1>|<action2>[:<role>]' "
            "avec ?key=value&key2=value2 optionnel"
        )

    scope = parts[0]
    actions_str = parts[1]
    role = parts[2] if len(parts) > 2 else None

    # Déterminer l'opérateur et splitter les actions
    if "/" in actions_str and "|" not in actions_str:
        operator = "&"  # AND
        actions_list = [a for a in actions_str.split("/") if a]
    elif "|" in actions_str and "/" not in actions_str:
        operator = "|"  # OR
        actions_list = [a for a in actions_str.split("|") if a]
    elif "/" in actions_str and "|" in actions_str:
        raise ValueError(
            f"Format de permission ambigu: '{perm}'. "
            "Utilisez soit '/' (AND) soit '|' (OR), pas les deux simultanément."
        )
    else:
        # Action unique (ni / ni |)
        operator = "&"  # par défaut : AND sur une seule action
        actions_list = [actions_str]

    return scope, actions_list, operator, role, query_context


def str_check(user: AbstractBaseUser, perm: str, **context: Any) -> bool:
    """
    Vérifie si un utilisateur possède les permissions requises à partir d'une chaîne formatée.

    La chaîne peut utiliser :
        - ``/`` (AND) : toutes les actions sont requises
        - ``|`` (OR) : au moins une action est requise

    Args:
        user: L'utilisateur dont on vérifie les permissions
        perm: Chaîne de permission au format
              ``<scope>:<action1>/<action2>:<role>?key=value`` (AND)
              ou ``<scope>:<action1>|<action2>:<role>?key=value`` (OR)
        **context: Contexte additionnel pour filtrer les grants (fusionné avec les query params)

    Returns:
        True si l'utilisateur possède les permissions requises, False sinon

    Example:
        >>> # Vérification AND : doit avoir create ET approve
        >>> str_check(user, 'orders:create/approve')
        True
        >>> # Vérification OR : doit avoir create OU approve
        >>> str_check(user, 'orders:create|approve')
        True
        >>> # Avec rôle et contexte
        >>> str_check(user, 'orders:create/approve:manager?tenant_id=42')
        False
    """
    from .caches import cache_check, cache_any_action_check

    # Parser la chaîne de permission (nouveau format avec opérateur)
    scope, required, operator, role, query_context = parse_permission(perm)

    # Fusionner les contextes (kwargs ont priorité sur query params)
    final_context = {**query_context, **context}

    if operator == "|":
        return cache_any_action_check(user, scope, required, role=role, **final_context)
    else:
        return cache_check(user, scope, required, role=role, **final_context)


def load_preset(*, force: bool = False) -> dict[str, dict[str, int]]:
    """
    Synchronise the database with ``settings.PERMISSION_PRESET``.

    This function is **idempotent** — it can be run repeatedly without
    creating duplicates.  Existing objects are diffed and updated when
    their configuration changed; new objects are created.

    Nothing is ever deleted (destructive operations must be done manually).

    Args:
        force: Ignored (kept for backward compatibility).  The function
               always runs in sync mode now.

    Returns:
        Dict with per-entity statistics::

            {
                "roles":     {"created": N, "updated": N},
                "groups":    {"created": N, "updated": N},
                "role_grants": {"created": N, "updated": N},
            }

    Raises:
        AttributeError: If ``PERMISSION_PRESET`` is not defined.
        KeyError: If a required key is missing in the preset.
        ValueError: If a referenced role does not exist.
    """
    from django.conf import settings

    preset = getattr(settings, "PERMISSION_PRESET", None)
    if preset is None:
        raise AttributeError("PERMISSION_PRESET is not defined in Django settings")

    stats: dict[str, dict[str, int]] = {
        "roles": {"created": 0, "updated": 0},
        "groups": {"created": 0, "updated": 0},
        "role_grants": {"created": 0, "updated": 0},
    }

    # ── local caches to avoid repeated DB round-trips ──────────────
    roles_cache: dict[str, Role] = {}
    groups_cache: dict[str, Group] = {}

    # ── 1. Roles ───────────────────────────────────────────────────
    roles_data: list[dict] = preset.get("roles", [])
    for role_data in roles_data:
        slug = role_data["slug"]
        defaults = {"name": role_data["name"]}
        if "app" in role_data:
            defaults["app"] = role_data["app"]

        role, created = Role.objects.get_or_create(
            slug=slug, defaults=defaults
        )
        roles_cache[slug] = role

        if created:
            stats["roles"]["created"] += 1
        else:
            # Diff existing role — update if anything changed
            updated = False
            if role.name != defaults["name"]:
                role.name = defaults["name"]
                updated = True
            new_app = defaults.get("app")
            if role.app != new_app:
                role.app = new_app
                updated = True
            if updated:
                role.save(update_fields=["name", "app", "updated_at"])
                stats["roles"]["updated"] += 1

    # ── 2. Groups ──────────────────────────────────────────────────
    groups_data: list[dict] = preset.get("groups", [])
    for group_data in groups_data:
        slug = group_data["slug"]
        name = group_data["name"]
        defaults: dict = {"name": name}
        if "app" in group_data:
            defaults["app"] = group_data["app"]

        # ── Robust lookup: get_or_create is safe now that Group.save()
        # no longer overwrites an explicitly provided slug.
        # If a pre-existing entry has a different slug (from the old
        # buggy save()), it is left untouched — a new group with the
        # correct preset slug is created alongside it.
        group, created = Group.objects.get_or_create(
            slug=slug, defaults=defaults
        )

        groups_cache[slug] = group

        if created:
            stats["groups"]["created"] += 1
        else:
            updated = False
            if group.name != defaults["name"]:
                group.name = defaults["name"]
                updated = True
            new_app = defaults.get("app")
            if group.app != new_app:
                group.app = new_app
                updated = True
            if updated:
                group.save(update_fields=["name", "app", "updated_at"])
                stats["groups"]["updated"] += 1

        # ── Sync group ↔ role M2M ──────────────────────────────
        expected_role_slugs: set[str] = set(group_data.get("roles", []))
        # Validate all referenced roles exist
        for role_slug in expected_role_slugs:
            if role_slug not in roles_cache:
                raise ValueError(
                    f"Role '{role_slug}' referenced by group '{slug}' "
                    f"does not exist in the preset"
                )

        current_role_slugs: set[str] = set(
            group.roles.values_list("slug", flat=True)
        )

        if expected_role_slugs != current_role_slugs:
            to_add = expected_role_slugs - current_role_slugs
            to_remove = current_role_slugs - expected_role_slugs

            if to_remove:
                group.roles.remove(
                    *[roles_cache[s] for s in to_remove]
                )
            if to_add:
                group.roles.add(
                    *[roles_cache[s] for s in to_add]
                )

    # ── 3. Role grants ────────────────────────────────────────────
    role_grants_data: list[dict] = preset.get("role_grants", [])
    for rg_data in role_grants_data:
        role_slug = rg_data["role"]
        role = roles_cache.get(role_slug)
        if role is None:
            raise ValueError(
                f"Role '{role_slug}' referenced by a role_grant "
                f"does not exist in the preset"
            )

        new_actions: list[str] = rg_data.get("actions", [])
        new_context: dict = rg_data.get("context", {})

        role_grant, created = RoleGrant.objects.get_or_create(
            role=role,
            scope=rg_data["scope"],
            defaults={"actions": new_actions, "context": new_context},
        )

        if created:
            stats["role_grants"]["created"] += 1
        else:
            # Diff: compare sorted actions and context
            if (
                sorted(role_grant.actions) != sorted(new_actions)
                or role_grant.context != new_context
            ):
                role_grant.actions = new_actions
                role_grant.context = new_context
                role_grant.save(update_fields=["actions", "context"])
                stats["role_grants"]["updated"] += 1

    return stats
