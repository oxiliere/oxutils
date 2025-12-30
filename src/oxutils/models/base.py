import uuid
import time
from django.db import models
from django.db import transaction
from django.conf import settings
from oxutils.models.fields import MaskedBackupField



try:
    from safedelete.models import SafeDeleteModel
    from safedelete.models import SOFT_DELETE_CASCADE
    from safedelete.signals import post_undelete
except ImportError:
    from django.dispatch import Signal
    post_undelete = Signal()
    SOFT_DELETE_CASCADE = 2

    class SafeDeleteModel(models.Model):
        def __new__(cls, *args, **kwargs):
            raise ImportError("django-safedelete is not installed, please install it to use SafeDeleteModel")


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


class SafeDeleteModelMixin(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE
    mask_fields = []

    _masked_backup = MaskedBackupField(default=dict, editable=False)

    class Meta:
        abstract = True

    @transaction.atomic
    def delete(self, *args, **kwargs):
        backup = {}

        for field_name in self.mask_fields:
            field = self._meta.get_field(field_name)
            old_value = getattr(self, field_name)

            if old_value is None:
                continue

            backup[field_name] = old_value
            masked = self._mask_value(field, old_value)
            setattr(self, field_name, masked)

        if backup:
            self._masked_backup = backup
            self.save(update_fields=[*backup.keys(), "_masked_backup"])

        return super().delete(*args, **kwargs)

    def _mask_value(self, field: models.Field, old_value):
        uid = uuid.uuid4().hex
        ts = int(time.time())

        if isinstance(field, models.EmailField):
            return f"{ts}.{uid}.deleted@invalid.local"

        if isinstance(field, models.URLField):
            return f"https://deleted.invalid/{ts}/{uid}"

        if isinstance(field, models.SlugField):
            return f"deleted-{ts}-{uid}"

        if isinstance(field, models.CharField):
            return f"__deleted__{ts}__{uid}"

        if isinstance(field, models.IntegerField):
            return None  # souvent OK, sinon adapte

        # fallback générique
        return f"deleted-{ts}-{uid}"

    @transaction.atomic
    def restore_masked_fields(self):
        if not self._masked_backup:
            return

        for field_name, old_value in self._masked_backup.items():
            field = self._meta.get_field(field_name)

            # vérification collision
            qs = self.__class__._default_manager.filter(
                **{field_name: old_value}
            ).exclude(pk=self.pk)

            if qs.exists():
                raise ValueError(
                    f"Collision détectée lors de la restauration du champ '{field_name}'"
                )

            setattr(self, field_name, old_value)

        self._masked_backup = {}
        self.save()


def _restore_masked_fields(sender, instance, **kwargs):
    if isinstance(instance, SafeDeleteModelMixin):
        instance.restore_masked_fields()


post_undelete.connect(_restore_masked_fields)
