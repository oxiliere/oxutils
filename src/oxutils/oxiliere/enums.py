from django.db.models import TextChoices


class TenantStatus(TextChoices):
    PENDING_MIGRATION = "pending_migration"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    REMOVED = "removed"
