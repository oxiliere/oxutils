from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models, transaction
from oxutils.enums.audit import ExportStatus
from oxutils.models.base import TimestampMixin
from oxutils.s3.storages import LogStorage




class LogExportHistory(models.Model):
    state = models.ForeignKey(
        "LogExportState",
        related_name='log_histories',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        default=ExportStatus.PENDING,
        choices=(
            (ExportStatus.FAILED, _("Failed")),
            (ExportStatus.PENDING, _('Pending')),
            (ExportStatus.SUCCESS, _('Success'))
        )
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when this record was created"
    )


class LogExportState(TimestampMixin):
    last_export_date = models.DateTimeField(null=True)
    status = models.CharField(
        default=ExportStatus.PENDING,
        choices=(
            (ExportStatus.FAILED, _("Failed")),
            (ExportStatus.PENDING, _('Pending')),
            (ExportStatus.SUCCESS, _('Success'))
        )
    )
    data = models.FileField(storage=LogStorage())
    size = models.BigIntegerField()

    @classmethod
    def create(cls, size: int = 0):
        return cls.objects.create(
            status=ExportStatus.PENDING,
            size=size
        )

    @transaction.atomic
    def set_success(self):
        self.status = ExportStatus.SUCCESS
        self.last_export_date = timezone.now()
        LogExportHistory.objects.create(
            state=self,
            status=ExportStatus.SUCCESS
        )
        self.save(update_fields=(
            'status',
            'last_export_date',
            'updated_at'
        ))

    @transaction.atomic
    def set_failed(self):
        self.status = ExportStatus.FAILED
        self.save(update_fields=(
            'status',
            'updated_at'
        ))
        LogExportHistory.objects.create(
            state=self,
            status=ExportStatus.FAILED
        )
