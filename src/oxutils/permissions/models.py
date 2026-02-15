from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from oxutils.models import TimestampMixin
from .actions import expand_actions




class Role(TimestampMixin):
    """
    A role.
    """
    slug = models.SlugField(unique=True, primary_key=True)
    app = models.CharField(max_length=25, null=True, blank=True)
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
    app = models.CharField(max_length=25, null=True, blank=True)
    roles = models.ManyToManyField(Role, related_name="groups")

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=['app'])
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
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="grants")
    scope = models.CharField(max_length=100)
    actions = ArrayField(models.CharField(max_length=5))
    context = models.JSONField(default=dict, blank=True)

    def clean(self):
        self.actions = expand_actions(self.actions)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "scope"], name="unique_role_scope"
            )
        ]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["role", "scope"]),
        ]
        ordering = ["role__slug", "scope"]

    def __str__(self):
        return f"{self.role}:{self.scope}:{self.actions}"


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Grant(TimestampMixin):
    """
    A grant of permissions to a user.
    
    - locked = False: Inherited from RoleGrant, can be modified by group_sync
    - locked = True: Custom grant (via override_grant), protected from group_sync
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="grants",
    )

    # traçabilité
    role = models.ForeignKey(
        Role,
        related_name="user_grants",
        on_delete=models.CASCADE,
    )

    locked = models.BooleanField(default=False, help_text="Si True, ce grant ne sera pas modifié par group_sync")
    
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
            models.Index(fields=["locked"]),
            GinIndex(fields=["actions"]),
            GinIndex(fields=["context"]),
        ]
        ordering = ["scope"]

    def __str__(self):
        return f"{self.user} {self.scope} {self.actions}"
