"""
Export utilities for audit logs.

This module provides utilities to export LogEntry records from auditlog,
compress them into ZIP files, and save them to LogExportState.
"""
import io
import json
import zipfile
from datetime import datetime
from typing import Optional

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models import QuerySet
from django.utils import timezone

from oxutils.audit.models import LogExportState


def get_logentry_model():
    """Get the LogEntry model from auditlog."""
    return apps.get_model('auditlog', 'LogEntry')


def export_logs_from_date(
    from_date: datetime,
    to_date: Optional[datetime] = None,
    batch_size: int = 5000
) -> LogExportState:
    """
    Export audit logs from a specific date, compress them, and save to LogExportState.
    Optimized for S3 storage with streaming and minimal memory usage.
    
    Args:
        from_date: Start date for log export (inclusive)
        to_date: End date for log export (inclusive). If None, uses current time.
        batch_size: Number of records to process at a time (default: 5000)
        
    Returns:
        LogExportState: The created export state with the compressed data
        
    Raises:
        Exception: If export fails, the LogExportState status will be set to FAILED
    """
    if to_date is None:
        to_date = timezone.now()
    
    # Create the export state
    export_state = LogExportState.create(size=0)
    
    try:
        # Get LogEntry model
        LogEntry = get_logentry_model()
        
        # Query logs within date range - use select_related for optimization
        logs_queryset = LogEntry.objects.filter(
            timestamp__gte=from_date,
            timestamp__lte=to_date
        ).select_related('content_type', 'actor').order_by('timestamp')
        
        # Create ZIP file in memory with optimal compression
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            # Export logs in batches using iterator to avoid loading all in memory
            total_exported = 0
            batch_number = 1
            batch_logs = []
            
            # Use iterator() to stream results from database
            for log in logs_queryset.iterator(chunk_size=batch_size):
                batch_logs.append(_serialize_log_entry(log))
                
                # Write batch when it reaches batch_size
                if len(batch_logs) >= batch_size:
                    filename = f'logs_batch_{batch_number:04d}.json'
                    # Use separators to minimize JSON size
                    zip_file.writestr(
                        filename, 
                        json.dumps(batch_logs, separators=(',', ':'))
                    )
                    total_exported += len(batch_logs)
                    batch_number += 1
                    batch_logs = []
            
            # Write remaining logs
            if batch_logs:
                filename = f'logs_batch_{batch_number:04d}.json'
                zip_file.writestr(
                    filename, 
                    json.dumps(batch_logs, separators=(',', ':'))
                )
                total_exported += len(batch_logs)
            
            # Export metadata at the end (we now have accurate count)
            metadata = {
                'export_date': timezone.now().isoformat(),
                'from_date': from_date.isoformat(),
                'to_date': to_date.isoformat(),
                'total_records': total_exported,
                'batch_size': batch_size,
                'total_batches': batch_number
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, separators=(',', ':')))
        
        # Get the ZIP file size and content
        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        zip_size = len(zip_content)
        
        # Save to LogExportState - S3 upload happens here
        filename = f'audit_logs_{from_date.strftime("%Y%m%d")}_{to_date.strftime("%Y%m%d")}.zip'
        export_state.data.save(filename, ContentFile(zip_content), save=False)
        export_state.size = zip_size
        export_state.set_success()
        
        return export_state
        
    except Exception as e:
        export_state.set_failed()
        raise e


def _serialize_log_entry(log) -> dict:
    """
    Serialize a single LogEntry to a dictionary (optimized version).
    
    Args:
        log: LogEntry object
        
    Returns:
        dict: Serialized log entry with minimal overhead
    """
    return {
        'id': log.id,
        'timestamp': log.timestamp.isoformat() if log.timestamp else None,
        'action': log.action,
        'content_type': {
            'app_label': log.content_type.app_label if log.content_type else None,
            'model': log.content_type.model if log.content_type else None,
        } if log.content_type else None,
        'object_pk': log.object_pk,
        'object_repr': log.object_repr,
        'changes': log.changes,
        'actor': {
            'id': log.actor.id if log.actor else None,
            'username': str(log.actor) if log.actor else None,
        } if log.actor else None,
        'remote_addr': log.remote_addr,
        'additional_data': log.additional_data if hasattr(log, 'additional_data') else None,
    }


def serialize_log_entries(queryset: QuerySet) -> list:
    """
    Serialize LogEntry queryset to a list of dictionaries.
    
    Args:
        queryset: QuerySet of LogEntry objects
        
    Returns:
        list: List of serialized log entries
    """
    return [_serialize_log_entry(log) for log in queryset]


def export_logs_since_last_export(batch_size: int = 5000) -> Optional[LogExportState]:
    """
    Export logs since the last successful export.
    
    Args:
        batch_size: Number of records to process at a time
        
    Returns:
        LogExportState or None: The created export state, or None if no previous export exists
    """
    # Get the last successful export
    last_export = LogExportState.objects.filter(
        status='success',
        last_export_date__isnull=False
    ).order_by('-last_export_date').first()
    
    if last_export:
        from_date = last_export.last_export_date
    else:
        # If no previous export, start from the earliest log
        LogEntry = get_logentry_model()
        earliest_log = LogEntry.objects.order_by('timestamp').first()
        
        if not earliest_log:
            return None
        
        from_date = earliest_log.timestamp
    
    return export_logs_from_date(from_date=from_date, batch_size=batch_size)


def get_export_statistics() -> dict:
    """
    Get statistics about log exports.
    
    Returns:
        dict: Statistics including total exports, successful exports, failed exports, etc.
    """
    from oxutils.enums.audit import ExportStatus
    
    total_exports = LogExportState.objects.count()
    successful_exports = LogExportState.objects.filter(status=ExportStatus.SUCCESS).count()
    failed_exports = LogExportState.objects.filter(status=ExportStatus.FAILED).count()
    pending_exports = LogExportState.objects.filter(status=ExportStatus.PENDING).count()
    
    last_export = LogExportState.objects.filter(
        status=ExportStatus.SUCCESS
    ).order_by('-last_export_date').first()
    
    total_size = sum(
        export.size for export in LogExportState.objects.filter(status=ExportStatus.SUCCESS)
    )
    
    return {
        'total_exports': total_exports,
        'successful_exports': successful_exports,
        'failed_exports': failed_exports,
        'pending_exports': pending_exports,
        'last_export_date': last_export.last_export_date if last_export else None,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
    }
