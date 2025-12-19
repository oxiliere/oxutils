"""
Utility functions for audit logging.
"""
import structlog


def get_request_id():
    """
    Get the request_id from django-structlog context.
    
    This function retrieves the request_id that was set by 
    django-structlog's RequestMiddleware and returns it for use
    in auditlog's correlation ID field.
    
    Returns:
        str: The request_id from the current request context, or None if not available.
    """
    try:
        context = structlog.contextvars.get_contextvars()
        return context.get('request_id')
    except Exception:
        return None
