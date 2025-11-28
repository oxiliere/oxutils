from django.conf import settings
from urllib.parse import urljoin
from ninja.files import UploadedFile
from ninja_extra.exceptions import ValidationError



def get_absolute_url(url: str, request=None):
    if request:
        # Build absolute URL using request
        return request.build_absolute_uri(url)
    else:
        # Fallback: build URL using MEDIA_URL and domain
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return urljoin(base_url, url)


def request_is_bound(request):
    """
    Check if a request is bound (has data), similar to Django Form.is_bound.
    """
    
    if not request or not hasattr(request, 'method'):
        return False
    
    if hasattr(request, 'data'):
        return (
            request.data is not None or
            bool(getattr(request, 'FILES', {})) or
            request.method in ('POST', 'PUT', 'PATCH')
        )
    
    elif hasattr(request, 'POST'):
        return (
            len(getattr(request, 'POST', {})) > 0 or
            len(getattr(request, 'FILES', {})) > 0 or
            request.method in ('POST', 'PUT', 'PATCH')
        )
    
    return False


def get_request_data(request):
    """
    Extract data from request, similar to how Django Forms get their data.
    
    Args:
        request: Django HttpRequest or DRF Request object
        
    Returns:
        dict: Request data (empty dict if no data)
    """
    if not request:
        return {}
    
    # DRF Request
    if hasattr(request, 'data'):
        return request.data or {}
    
    # Django HttpRequest
    elif hasattr(request, 'POST'):
        return dict(request.POST) if request.POST else {}
    
    return {}


def validate_image(image: UploadedFile, size: int = 2):
    """Validate uploaded image file"""
    # Check file size (2MB = 2 * 1024 * 1024 bytes)
    MAX_FILE_SIZE = size * 1024 * 1024  # 2MB
    if image.size > MAX_FILE_SIZE:
        raise ValidationError(f"La taille du fichier ne peut pas dépasser 2MB. Taille actuelle: {image.size / (1024 * 1024):.1f}MB")
    
    # Check file type
    ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if image.content_type not in ALLOWED_TYPES:
        raise ValidationError(f"Type de fichier non supporté. Types autorisés: {', '.join(ALLOWED_TYPES)}")
    
    # Check file extension
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = image.name.lower().split('.')[-1] if '.' in image.name else ''
    if f'.{file_extension}' not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Extension de fichier non supportée. Extensions autorisées: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Additional validation: check if file is actually an image
    try:
        from PIL import Image
        import io
        
        # Reset file pointer to beginning
        image.seek(0)
        image = Image.open(io.BytesIO(image.read()))
        image.verify()  # Verify it's a valid image
        
        # Reset file pointer again for later use
        image.seek(0)
        
    except Exception as e:
        raise ValidationError("Le fichier n'est pas une image valide")
