from uuid import UUID

import structlog

from django.db.models import QuerySet

from oxutils.mixins.services import BaseService
from oxutils.oxiliere.utils import get_tenant_user_model


logger = structlog.get_logger(__name__)


class TenantUserService(BaseService):

    logger = logger

    def _get_queryset(self) -> QuerySet:
        TenantUser = get_tenant_user_model()
        return TenantUser.objects.select_related('user')

    def list(self) -> QuerySet:
        return self._get_queryset().all().order_by('user__first_name')

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

    def set_admin(self, pk: UUID, is_admin: bool):
        tenant_user = self.get(pk)
        tenant_user.is_admin = is_admin
        tenant_user.save(update_fields=['is_admin'])
        self.logger.info("tenant_user_set_admin", pk=pk, is_admin=is_admin)
        return tenant_user

    def set_owner(self, pk: UUID, is_owner: bool):
        tenant_user = self.get(pk)
        tenant_user.is_owner = is_owner
        tenant_user.save(update_fields=['is_owner'])
        self.logger.info("tenant_user_set_owner", pk=pk, is_owner=is_owner)
        return tenant_user

    def remove(self, pk: UUID):
        tenant_user = self.get(pk)
        tenant_user.delete()
        # TODO: notify tenant owner and removed user
        self.logger.info("tenant_user_removed", pk=pk)
