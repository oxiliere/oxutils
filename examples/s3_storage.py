"""
S3 Storage Example

Shows how to use different S3 storage backends.
"""

from django.db import models
from oxutils.s3.storages import PrivateMediaStorage, PublicMediaStorage

# 1. Public media (user avatars, product images)
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/')
    # Uses PublicMediaStorage by default (if configured)
    # URL: https://cdn.example.com/media/avatars/image.jpg

# 2. Private media (invoices, contracts)
class Invoice(models.Model):
    customer = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    pdf = models.FileField(
        storage=PrivateMediaStorage(),
        upload_to='invoices/%Y/%m/'
    )
    
    def get_download_url(self):
        """Get presigned URL (valid 1 hour)."""
        return self.pdf.url

# 3. Usage in views
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse

def download_invoice(request, invoice_id):
    """Download invoice with access control."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Check permissions
    if invoice.customer != request.user:
        return HttpResponse('Unauthorized', status=403)
    
    # Redirect to presigned URL
    return redirect(invoice.get_download_url())

# 4. Direct storage operations
from django.core.files.base import ContentFile

def save_report(content: bytes, filename: str):
    """Save report to private storage."""
    storage = PrivateMediaStorage()
    path = storage.save(f'reports/{filename}', ContentFile(content))
    url = storage.url(path)  # Presigned URL
    return url
