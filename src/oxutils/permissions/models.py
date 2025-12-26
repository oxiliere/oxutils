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


class Group(TimestampMixin):
    """
    A group of roles. for UI Template purposes.
    """
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    roles = models.ManyToManyField(Role, related_name="groups")

    def __str__(self):
        return self.slug


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

    def __str__(self):
        return f"{self.role}:{self.scope}:{self.actions}"


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
        on_delete=models.SET_NULL,
    )

    scope = models.CharField(max_length=100)
    actions = ArrayField(models.CharField(max_length=5))
    context = models.JSONField(default=dict, blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "scope", "role"], name="unique_user_scope_role"
            )
        ]
        indexes = [
            models.Index(fields=["user", "scope"]),
            GinIndex(fields=["actions"]),
            GinIndex(fields=["context"]),
        ]

    def __str__(self):
        return f"{self.user} {self.scope} {self.actions}"
