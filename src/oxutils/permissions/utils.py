from typing import Optional, Any
from django.db.models import QuerySet, Q
from django.db import transaction
from django.contrib.auth.models import AbstractBaseUser

from .models import Grant, RoleGrant, Group
from .actions import expand_actions, collapse_actions




@transaction.atomic
def assign_role(
    user: AbstractBaseUser,
    role: str,
    *,
    by: Optional[AbstractBaseUser] = None
) -> None:
    """
    Assigne un rôle à un utilisateur en créant ou mettant à jour les grants correspondants.
    
    Args:
        user: L'utilisateur à qui assigner le rôle
        role: Le slug du rôle à assigner
        by: L'utilisateur qui effectue l'assignation (pour traçabilité)
    """
    role_grants: QuerySet[RoleGrant] = RoleGrant.objects.filter(role__slug=role)

    for rg in role_grants:
        Grant.objects.update_or_create(
            user=user,
            scope=rg.scope,
            role=role,
            defaults={
                "actions": expand_actions(rg.actions),
                "context": rg.context,
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
    """
    return Grant.objects.filter(
        user__pk=user.pk,
        role__slug=role
    ).delete()


def assign_group(user: AbstractBaseUser, group: str) -> None:
    """
    Assigne tous les rôles d'un groupe à un utilisateur.
    
    Args:
        user: L'utilisateur à qui assigner le groupe
        group: Le slug du groupe à assigner
        
    Raises:
        Group.DoesNotExist: Si le groupe n'existe pas
    """
    _group: Group = Group.objects.get(slug=group)

    for role in _group.roles.all():
        assign_role(user, role.slug)


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
    """
    grant: Optional[Grant] = Grant.objects.filter(user__pk=user.pk, scope=scope).first()
    if not grant:
        return

    # Réduire les actions aux actions racines
    root_actions: set[str] = collapse_actions(grant.actions)
    # Expander les actions à retirer pour inclure leurs dépendances
    expanded_remove: list[str] = expand_actions(remove_actions)

    # Retirer les actions demandées
    root_actions = {
        a for a in root_actions if a not in expanded_remove
    }

    # Si plus d'actions, supprimer le grant
    if not root_actions:
        grant.delete()
        return

    # Mettre à jour le grant avec les nouvelles actions
    grant.actions = expand_actions(list(root_actions))
    grant.role = None  # Le grant devient personnalisé
    grant.save(update_fields=["actions", "role", 'updated_at'])


def check(
    user: AbstractBaseUser,
    scope: str,
    required: list[str],
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
        **context: Contexte additionnel pour filtrer les grants (clés JSON)
        
    Returns:
        True si l'utilisateur possède toutes les actions requises, False sinon
        
    Example:
        >>> # Vérifier si l'utilisateur peut lire les articles
        >>> check(user, 'articles', ['r'])
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
    
    # Ajouter les filtres de contexte si fournis
    if context:
        grant_filter &= Q(context__contains=context)
    
    # Vérifier l'existence d'un grant correspondant
    return Grant.objects.filter(grant_filter).exists()


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
            },
            {
                "role": "accountant",
                "scope": "users",
                "actions": ["r"],
                "context": {}
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
        role, created = Role.objects.get_or_create(
            slug=role_data['slug'],
            defaults={'name': role_data['name']}
        )
        roles_cache[role.slug] = role
        if created:
            stats['roles'] += 1
    
    # Créer les groupes et peupler le cache
    groups_data = preset.get('group', [])
    for group_data in groups_data:
        group, created = Group.objects.get_or_create(
            slug=group_data['slug'],
            defaults={'name': group_data['name']}
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
        
        role_grant, created = RoleGrant.objects.get_or_create(
            role=role,
            scope=rg_data['scope'],
            defaults={
                'actions': rg_data.get('actions', []),
                'context': rg_data.get('context', {})
            }
        )
        if created:
            stats['role_grants'] += 1
    
    return stats
