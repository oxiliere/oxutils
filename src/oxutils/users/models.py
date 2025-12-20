from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE
from auditlog.registry import auditlog
from oxutils.models import BaseModelMixin



class UserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User
    """
    def create_user(self, email, oxi_id, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et l'oxi_id donnés.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not oxi_id:
            raise ValueError(_('The oxi_id field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, oxi_id=oxi_id, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, oxi_id, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec l'email et l'oxi_id donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, oxi_id, **extra_fields)


class User(AbstractUser, SafeDeleteModel, BaseModelMixin):
    """
    Modèle d'utilisateur personnalisé qui utilise l'email comme identifiant unique
    et intègre la suppression sécurisée (soft delete)
    """
    _safedelete_policy = SOFT_DELETE_CASCADE
    
    # Suppression du champ username qui est obligatoire dans AbstractUser
    username = None
    password = None # Don't need password

    oxi_id = models.UUIDField(unique=True)  # id venant de auth.oxi.com
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.CharField(max_length=255, null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['oxi_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.email



# Enregistrement du modèle User pour l'audit logging
auditlog.register(User)
