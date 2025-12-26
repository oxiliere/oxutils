from typing import Any
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractBaseUser

from .models import Grant


class PermissionQuerySet(models.QuerySet):
    """
    QuerySet personnalisé pour filtrer des objets selon les permissions d'un utilisateur.
    Permet de filtrer des querysets en fonction des grants de permissions.
    """

    def allowed_for(
        self,
        user: AbstractBaseUser,
        scope: str,
        required_actions: list[str],
        **context: Any
    ) -> "PermissionQuerySet":
        """
        Filtre les objets si l'utilisateur a les permissions requises.
        Vérifie l'existence d'un grant valide avant de retourner le queryset.
        
        Args:
            user: L'utilisateur dont on vérifie les permissions
            scope: Le scope à vérifier (ex: 'articles', 'users')
            required_actions: Liste des actions requises (ex: ['r'], ['w', 'r'])
            **context: Contexte additionnel pour filtrer (ex: tenant_id=123)
            
        Returns:
            QuerySet complet si autorisé, QuerySet vide sinon
            
        Example:
            >>> Article.objects.allowed_for(user, 'articles', ['r'])
            >>> Article.objects.allowed_for(user, 'articles', ['w'], tenant_id=123)
        """
        # Construire le filtre pour vérifier l'existence d'un grant
        grant_filter = Q(
            user__pk=user.pk,
            scope=scope,
            actions__contains=list(required_actions),
        )
        
        # Ajouter les filtres de contexte si fournis
        if context:
            grant_filter &= Q(context__contains=context)
        
        # Si un grant existe, retourner le queryset complet, sinon vide
        if Grant.objects.filter(grant_filter).exists():
            return self
        return self.none()

    def denied_for(
        self,
        user: AbstractBaseUser,
        scope: str,
        required_actions: list[str],
        **context: Any
    ) -> "PermissionQuerySet":
        """
        Filtre les objets si l'utilisateur N'A PAS les permissions requises.
        Inverse de allowed_for.
        
        Args:
            user: L'utilisateur dont on vérifie les permissions
            scope: Le scope à vérifier
            required_actions: Liste des actions requises
            **context: Contexte additionnel pour filtrer
            
        Returns:
            QuerySet complet si NON autorisé, QuerySet vide si autorisé
            
        Example:
            >>> Article.objects.denied_for(user, 'articles', ['w'])
        """
        # Construire le filtre pour vérifier l'existence d'un grant
        grant_filter = Q(
            user__pk=user.pk,
            scope=scope,
            actions__contains=list(required_actions),
        )
        
        # Ajouter les filtres de contexte si fournis
        if context:
            grant_filter &= Q(context__contains=context)
        
        # Si un grant existe, retourner vide, sinon le queryset complet
        if Grant.objects.filter(grant_filter).exists():
            return self.none()
        return self
