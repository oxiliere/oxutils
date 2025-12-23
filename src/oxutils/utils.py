from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address from request metadata.

    Priority:

        1. X-Forwarded-For header (first entry if multiple)
        2. REMOTE_ADDR meta value

    Args:
        request (HttpRequest): Django request object

    Returns:
        str: Client IP address or None if not found
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

