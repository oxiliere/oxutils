from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from oxutils.models import TimestampMixin
from .actions import expand_actions




class Role(TimestampMixin):
    """
    A role.
    """
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.slug

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
        ]
        ordering = ["slug"]


class Group(TimestampMixin):
    """
    A group of roles. for UI Template purposes.
    """
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    roles = models.ManyToManyField(Role, related_name="groups")

    def __str__(self):
        return self.slug

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
        ]
        ordering = ["slug"]


class UserGroup(TimestampMixin):
    """
    A user group that links users to groups.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_groups",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="user_groups",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'group'], name='unique_user_group')
        ]
        indexes = [
            models.Index(fields=['user', 'group']),
        ]


class RoleGrant(models.Model):
    """
    A grant template of permissions to a role.
    Peut être lié à un groupe spécifique pour des comportements distincts.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="grants")
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="role_grants",
        help_text="Groupe optionnel pour des comportements spécifiques"
    )

    scope = models.CharField(max_length=100)
    actions = ArrayField(models.CharField(max_length=5))
    context = models.JSONField(default=dict, blank=True)

    def clean(self):
        self.actions = expand_actions(self.actions)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "scope", "group"], name="unique_role_scope_group"
            )
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["group"]),
            models.Index(fields=["role", "group"]),
        ]
        ordering = ["role__slug", "group__slug"]

    def __str__(self):
        group_str = f"[{self.group.slug}]" if self.group else ""
        return f"{self.role}:{self.scope}{group_str}:{self.actions}"


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Grant(TimestampMixin):
    """
    A grant of permissions to a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grants",
    )

    # traçabilité
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        related_name="user_grants",
        on_delete=models.SET_NULL,
    )
    
    # Lien avec UserGroup pour tracer l'origine du grant
    user_group = models.ForeignKey(
        'UserGroup',
        null=True,
        blank=True,
        related_name="grants",
        on_delete=models.SET_NULL,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="created_grants",
        on_delete=models.SET_NULL,
    )

    scope = models.CharField(max_length=100)
    actions = ArrayField(models.CharField(max_length=5))
    context = models.JSONField(default=dict, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "scope", "role", "user_group"], name="unique_user_scope_role"
            )
        ]
        indexes = [
            models.Index(fields=["user", "scope"]),
            models.Index(fields=["user_group"]),
            GinIndex(fields=["actions"]),
            GinIndex(fields=["context"]),
        ]
        ordering = ["scope"]

    def __str__(self):
        return f"{self.user} {self.scope} {self.actions}"
