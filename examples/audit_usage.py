"""
Example: Using the Audit Export Models

This example demonstrates how to use the audit export functionality
in your Django project.
"""

# First, add to your settings.py:
# INSTALLED_APPS = [
#     ...
#     'oxutils.audit',
# ]
#
# Then run migrations:
# python manage.py migrate audit

from datetime import datetime, timedelta
from oxutils.audit.export import export_logs_from_date
from oxutils.audit.models import LogExportState, LogExportHistory


def export_weekly_logs():
    """Export logs from the last 7 days."""
    from_date = datetime.now() - timedelta(days=7)
    
    # Create and execute export
    export_state = export_logs_from_date(from_date=from_date)
    
    print(f"Export Status: {export_state.status}")
    print(f"Export Size: {export_state.size} bytes")
    print(f"Export URL: {export_state.data.url}")
    
    return export_state


def check_export_history(export_state):
    """Check the history of an export."""
    histories = export_state.log_histories.all()
    
    for history in histories:
        print(f"History Entry: {history.status} at {history.created_at}")


def create_manual_export():
    """Create a manual export state."""
    # Create a new export state
    export_state = LogExportState.create(size=0)
    
    print(f"Created export state with ID: {export_state.id}")
    print(f"Initial status: {export_state.status}")
    
    # Simulate processing...
    # When successful:
    export_state.set_success()
    print(f"Updated status: {export_state.status}")
    
    # Or if failed:
    # export_state.set_failed()
    
    return export_state


def query_exports():
    """Query existing exports."""
    from oxutils.enums.audit import ExportStatus
    
    # Get all successful exports
    successful_exports = LogExportState.objects.filter(
        status=ExportStatus.SUCCESS
    )
    
    print(f"Found {successful_exports.count()} successful exports")
    
    # Get recent exports
    recent_exports = LogExportState.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=30)
    ).order_by('-created_at')
    
    for export in recent_exports[:5]:
        print(f"Export {export.id}: {export.status} - {export.size} bytes")


if __name__ == '__main__':
    # Example usage
    print("=== Exporting Weekly Logs ===")
    export_state = export_weekly_logs()
    
    print("\n=== Checking Export History ===")
    check_export_history(export_state)
    
    print("\n=== Creating Manual Export ===")
    manual_export = create_manual_export()
    
    print("\n=== Querying Exports ===")
    query_exports()
