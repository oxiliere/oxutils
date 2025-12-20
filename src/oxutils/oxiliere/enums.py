from django.db.models import TextChoices



class TenantStatus(TextChoices):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    DELETED = 'deleted'
    REMOVED = 'removed'
