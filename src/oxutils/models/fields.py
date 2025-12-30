"""# settings.py

FIELD_MASKING_CRYPTO_ENABLED = True  # switch global

# optionnel (recommandé)
FIELD_MASKING_KEY = env("FIELD_MASKING_KEY", default=None)

"""

import json
import base64
import hashlib
from django.utils.functional import cached_property
from django.conf import settings
from django.db import models





def get_field_masking_fernet():
    from cryptography.fernet import Fernet

    if not hasattr(settings, "FIELD_MASKING_CRYPTO_ENABLED") or not settings.FIELD_MASKING_CRYPTO_ENABLED:
        return None

    if not hasattr(settings, "FIELD_MASKING_KEY") or settings.FIELD_MASKING_KEY:
        return Fernet(settings.FIELD_MASKING_KEY)

    # fallback contrôlé
    digest = hashlib.sha256(
        (settings.SECRET_KEY + ":field-masking:v1").encode()
    ).digest()

    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)



class MaskedBackupField(models.TextField):
    """
    JSONField avec chiffrement optionnel
    """

    @cached_property
    def fernet(self):
        return get_field_masking_fernet()

    def get_prep_value(self, value):
        if value in (None, ""):
            return None

        raw = json.dumps(value).encode()

        if not self.fernet:
            return raw.decode()

        return self.fernet.encrypt(raw).decode()

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, dict):
            return value

        if value in (None, ""):
            return {}

        try:
            if self.fernet:
                decrypted = self.fernet.decrypt(value.encode())
                return json.loads(decrypted.decode())

            return json.loads(value)

        except Exception:
            # sécurité : ne jamais casser un fetch DB
            return {}
