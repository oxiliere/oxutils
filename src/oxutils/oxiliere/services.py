"""
Oxiliere services — TenantUser management + Tenant lifecycle.
"""
import structlog
from typing import Optional
from uuid import UUID

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from oxutils.mixins.services import BaseService
from oxutils.oxiliere.enums import TenantStatus
from oxutils.oxiliere.utils import get_tenant_user_model

logger = structlog.get_logger(__name__)


# ── TenantUserService (existing) ────────────────────────────────────

class TenantUserService(BaseService):
    logger = logger

    def _get_queryset(self) -> QuerySet:
        TenantUser = get_tenant_user_model()
        return TenantUser.objects.select_related("user")

    def list(self) -> QuerySet:
        return self._get_queryset().all().order_by("user__first_name")

    def get(self, pk: UUID):
        try:
            return self._get_queryset().get(pk=pk)
        except get_tenant_user_model().DoesNotExist as e:
            self.exception_handler(e, logger=self.logger)

    def update(self, pk: UUID, data: dict):
        tenant_user = self.get(pk)
        update_fields = []
        for field, value in data.items():
            setattr(tenant_user, field, value)
            update_fields.append(field)
        if update_fields:
            self.logger.info("tenant_user_updated", pk=pk, update_fields=update_fields)
            tenant_user.save(update_fields=update_fields)
        return tenant_user

    @transaction.atomic
    def set_admin(self, pk: UUID, is_admin: bool):
        tenant_user = self.get(pk)
        if tenant_user.is_admin == is_admin:
            return tenant_user
        try:
            if not is_admin:
                is_last_admin = self._get_queryset().filter(is_admin=True).count() == 1
                if is_last_admin:
                    raise ValueError(_("Cannot remove last admin"))
                tenant_user.is_admin = is_admin
                tenant_user.is_owner = False
                tenant_user.save(update_fields=["is_admin", "is_owner"])
                self.logger.info("tenant_user_set_admin", pk=pk, is_admin=is_admin, is_owner=False)
            else:
                tenant_user.is_admin = is_admin
                tenant_user.save(update_fields=["is_admin"])
                self.logger.info("tenant_user_set_admin", pk=pk, is_admin=is_admin)
        except Exception as e:
            self.exception_handler(e, logger=self.logger)
        return tenant_user

    @transaction.atomic
    def set_owner(self, pk: UUID, is_owner: bool):
        tenant_user = self.get(pk)
        if tenant_user.is_owner == is_owner:
            return tenant_user
        try:
            if not is_owner:
                is_last_owner = self._get_queryset().filter(is_owner=True).count() == 1
                if is_last_owner:
                    raise ValueError(_("Cannot remove last owner"))
                tenant_user.is_owner = is_owner
                tenant_user.save(update_fields=["is_owner"])
                self.logger.info("tenant_user_set_owner", pk=pk, is_owner=is_owner)
            else:
                tenant_user.is_owner = is_owner
                tenant_user.is_admin = True
                tenant_user.save(update_fields=["is_owner", "is_admin"])
                self.logger.info("tenant_user_set_owner", pk=pk, is_owner=is_owner, is_admin=True)
        except Exception as e:
            self.exception_handler(e, logger=self.logger)
        return tenant_user

    def remove(self, pk: UUID):
        tenant_user = self.get(pk)
        tenant_user.delete()
        self.logger.info("tenant_user_removed", pk=pk)


# ── TenantService (new) ─────────────────────────────────────────────

class TenantService:
    """Thin service layer for tenant lifecycle operations."""

    @staticmethod
    def activate(tenant) -> None:
        if tenant.status == TenantStatus.ACTIVE:
            return
        with transaction.atomic():
            tenant.transition_to(TenantStatus.ACTIVE)
            tenant.is_active = True
            tenant.save(update_fields=["status", "is_active"])

    @staticmethod
    def deactivate(tenant) -> None:
        if tenant.status == TenantStatus.INACTIVE:
            return
        tenant.transition_to(TenantStatus.INACTIVE)
        tenant.is_active = False
        tenant.save(update_fields=["status", "is_active"])

    @staticmethod
    def suspend(tenant) -> None:
        if tenant.status == TenantStatus.SUSPENDED:
            return
        tenant.transition_to(TenantStatus.SUSPENDED)
        tenant.is_active = False
        tenant.save(update_fields=["status", "is_active"])

    @staticmethod
    def add_user(tenant, user: AbstractBaseUser, is_owner: bool = False, is_admin: bool = False) -> None:
        tenant.add_user(user, is_owner=is_owner, is_admin=is_admin)

    @staticmethod
    def remove_user(tenant, user: AbstractBaseUser) -> None:
        tenant.remove_user(user)

    @staticmethod
    def provision(tenant, owner: AbstractBaseUser, activate: bool = False) -> None:
        with transaction.atomic():
            tenant.add_user(owner, is_owner=True, is_admin=True)
            if activate:
                TenantService.activate(tenant)
