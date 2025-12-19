from django.db.models import TextChoices


class CurrencySource(TextChoices):
    BCC = "bcc", "BCC"
    OXR = "oxr", "Open Exchange Rates"

