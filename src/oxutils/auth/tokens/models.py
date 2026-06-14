import secrets

from django.conf import settings
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from oxutils.auth.utils import import_callable


class Token(models.Model):
    """
    The default authorization token model.
    """

    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        """
        Save the token instance.

        If no key is provided, generates a cryptographically secure key.
        For new tokens, ensures they are inserted as new (not updated).
        """
        if not self.key:
            self.key = self.generate_key()
            # For new objects, force INSERT to prevent overwriting existing tokens
            if self._state.adding:
                kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return secrets.token_hex(20)

    def __str__(self):
        return self.key


class TokenProxy(Token):
    """
    Proxy mapping pk to user pk for use in admin.
    """

    @property
    def pk(self):
        return self.user_id

    class Meta:
        proxy = True
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")


TokenModel = import_callable(getattr(settings, "REST_AUTH_TOKEN_MODEL", Token))


class BaseToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    created = models.DateTimeField(_("created"), auto_now_add=True)
    ip = models.GenericIPAddressField(_("ip"), blank=True, null=True, max_length=39)
    is_mobile = models.BooleanField(_("is mobile"), null=True)
    is_tablet = models.BooleanField(_("is tablet"), null=True)
    is_pc = models.BooleanField(_("is pc"), null=True)
    is_bot = models.BooleanField(_("is bot"), null=True)
    browser = models.CharField(_("browser"), max_length=32, blank=True, null=True)
    browser_version = models.CharField(_("browser version"), max_length=32, blank=True, null=True)
    os = models.CharField(_("os"), max_length=32, blank=True, null=True)
    os_version = models.CharField(_("os version"), max_length=32, blank=True, null=True)
    device = models.CharField(_("device"), max_length=32, blank=True, null=True)
    device_brand = models.CharField(_("device brand"), max_length=32, blank=True, null=True)
    device_model = models.CharField(_("device model"), max_length=32, blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")


class RefreshTokenManager(models.Manager):
    def create(self, **kwargs):
        """
        Create a new refresh token with session limiting.

        Limits the number of distinct sessions per user based on JWT_ALL_AUTH_MAX_SESSIONS setting.
        When the limit is exceeded, removes the oldest sessions to make room for the new one.
        """
        user = kwargs.pop("user", None)
        if not user:
            return super().create(**kwargs)

        # Get max sessions setting (default to 4 if not set)
        max_sessions = getattr(settings, "JWT_ALL_AUTH_MAX_SESSIONS", 4)

        with transaction.atomic():
            current_sessions = (
                self.filter(user=user, enabled=True).values("session").distinct("session").count()
            )

            if current_sessions >= max_sessions:
                sessions_to_remove = (
                    self.filter(user=user, enabled=True)
                    .values("session")
                    .annotate(oldest_created=models.Min("created"))
                    .order_by("oldest_created")
                )

                sessions_to_delete_count = abs(current_sessions - max_sessions + 1)

                sessions_to_delete = list(
                    sessions_to_remove[:sessions_to_delete_count].values_list("session", flat=True)
                )

                self.filter(user=user, session__in=sessions_to_delete).delete()

            return super().create(**kwargs)


class AbstractRefreshToken(BaseToken):
    jti = models.CharField(_("jti"), max_length=32, blank=False)
    enabled = models.BooleanField(_("enabled"), default=True)
    session = models.CharField(_("session"), max_length=32, blank=False)

    objects = RefreshTokenManager()

    class Meta:
        abstract = True
        verbose_name = _("refresh token")
        verbose_name_plural = _("refresh tokens")


class RefreshTokenWhitelistModel(AbstractRefreshToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens_whitelist",
        verbose_name=_("user"),
    )


class GenericTokenModel(BaseToken):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generic_tokens",
        verbose_name=_("user"),
    )
    token = models.CharField(_("token"), max_length=255, blank=False)
    purpose = models.CharField(_("purpose"), max_length=32, blank=False)
