import uuid
from django.db import models
from django.conf import settings


class UUIDPrimaryKeyMixin(models.Model):
    """Mixin that provides a UUID primary key field."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record"
    )

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """Mixin that provides created_at and updated_at timestamp fields."""
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when this record was last updated"
    )

    class Meta:
        abstract = True


class UserTrackingMixin(models.Model):
    """Mixin that tracks which user created and last modified a record."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        help_text="User who last updated this record"
    )

    class Meta:
        abstract = True


class SlugMixin(models.Model):
    """Mixin that provides a slug field."""
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly version of the name"
    )

    class Meta:
        abstract = True


class NameMixin(models.Model):
    """Mixin that provides name and description fields."""
    name = models.CharField(
        max_length=255,
        help_text="Name of this record"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ActiveMixin(models.Model):
    """Mixin that provides an active/inactive status field."""
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this record is active"
    )

    class Meta:
        abstract = True


class OrderingMixin(models.Model):
    """Mixin that provides an ordering field."""
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order for sorting records"
    )

    class Meta:
        abstract = True
        ordering = ['order']


class BaseModelMixin(UUIDPrimaryKeyMixin, TimestampMixin, ActiveMixin):
    """
    Base mixin that combines the most commonly used mixins.
    Provides UUID primary key, timestamps, and active status.
    """
    class Meta:
        abstract = True
