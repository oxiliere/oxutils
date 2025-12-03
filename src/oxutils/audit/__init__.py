"""
Oxutils Audit Module

Provides audit log export functionality with S3 storage.
"""

# Models are imported lazily to avoid AppRegistryNotReady errors
# Use: from oxutils.audit.models import LogExportState, LogExportHistory

__all__ = [
    'LogExportState',
    'LogExportHistory',
]

def __getattr__(name):
    """Lazy import of models to avoid AppRegistryNotReady errors."""
    if name in __all__:
        from oxutils.audit.models import LogExportState, LogExportHistory
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
