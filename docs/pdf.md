# PDF Module

**WeasyPrint-based PDF generation for Django with template rendering**

## Features

- Class-based views for PDF responses
- Standalone `Printer` class for non-view contexts
- Django template rendering with context
- Custom CSS stylesheet support
- Static file integration (STATIC_URL and MEDIA_URL)
- Font configuration support
- Production-ready with helper utilities
- Compatible with Celery tasks and management commands

## Setup

### Installation

Add to your Django settings:

```python
# settings.py
from oxutils.conf import UTILS_APPS

INSTALLED_APPS = [
    *UTILS_APPS,  # Includes 'oxutils.pdf'
    # your apps...
]

# Configure base URL for WeasyPrint (important for static files)
WEASYPRINT_BASEURL = 'http://127.0.0.1:8000/'  # Development
# WEASYPRINT_BASEURL = 'https://yourdomain.com/'  # Production
```

### Dependencies

The module requires WeasyPrint:

```bash
pip install weasyprint>=60.0
```

## Components

### 1. WeasyTemplateView (Class-Based View)

Use for Django views that return PDF responses.

#### Basic Usage

```python
from oxutils.pdf import WeasyTemplateView

class InvoicePDFView(WeasyTemplateView):
    template_name = 'invoices/invoice_pdf.html'
    pdf_filename = 'invoice.pdf'
    pdf_attachment = True  # Force download, False for inline display
    pdf_stylesheets = []  # List of CSS files
    pdf_options = {}  # WeasyPrint options

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = Invoice.objects.get(pk=self.kwargs['pk'])
        return context
```

#### URL Configuration

```python
# urls.py
from django.urls import path
from .views import InvoicePDFView

urlpatterns = [
    path('invoice/<int:pk>/pdf/', InvoicePDFView.as_view(), name='invoice_pdf'),
]
```

#### Advanced Configuration

```python
class ReportPDFView(WeasyTemplateView):
    template_name = 'reports/report.html'
    
    def get_pdf_filename(self):
        """Dynamic filename based on context"""
        report = self.get_report()
        return f'report_{report.id}_{report.date}.pdf'
    
    def get_pdf_stylesheets(self):
        """Dynamic stylesheets"""
        from django.contrib.staticfiles.finders import find
        css_path = find('css/report.css')
        return [css_path] if css_path else []
    
    def get_pdf_options(self):
        """Custom WeasyPrint options"""
        return {
            'pdf_forms': True,
            'uncompressed_pdf': False,
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.get_report()
        return context
    
    def get_report(self):
        return Report.objects.get(pk=self.kwargs['pk'])
```

### 2. Printer (Standalone Class)

Use for PDF generation outside of views (Celery tasks, management commands, scripts).

#### Basic Usage

```python
from oxutils.pdf import Printer

# Create printer instance
printer = Printer(
    template_name='documents/certificate.html',
    context={'name': 'John Doe', 'date': '2025-12-21'},
    stylesheets=[],  # Optional CSS files
    options={},      # Optional WeasyPrint options
    base_url=None    # Optional base URL override
)

# Generate PDF bytes
pdf_bytes = printer.write_pdf()

# Or write to file
with open('certificate.pdf', 'wb') as f:
    printer.write_object(f)
```

#### With BytesIO (for Django FileField)

```python
import io
from django.core.files.base import ContentFile
from oxutils.pdf import Printer

# Generate PDF
printer = Printer(
    template_name='cv/template.html',
    context={'profile': profile}
)

# Write to BytesIO
obj = io.BytesIO()
printer.write_pdf(output=obj)

# Save to FileField
profile.curriculum_vitae.save(
    'cv.pdf',
    ContentFile(obj.getvalue()),
    save=True
)
```

#### In Celery Tasks

```python
from celery import shared_task
from oxutils.pdf import Printer
from django.core.files.base import ContentFile

@shared_task
def generate_monthly_report(report_id):
    report = Report.objects.get(id=report_id)
    
    printer = Printer(
        template_name='reports/monthly.html',
        context={'report': report},
        stylesheets=get_stylesheets('css/report.css')
    )
    
    obj = io.BytesIO()
    printer.write_pdf(output=obj)
    
    report.pdf_file.save(
        f'report_{report.month}.pdf',
        ContentFile(obj.getvalue()),
        save=True
    )
    
    return f"Report {report_id} generated"
```

#### In Management Commands

```python
from django.core.management.base import BaseCommand
from oxutils.pdf import Printer

class Command(BaseCommand):
    help = 'Generate all pending certificates'
    
    def handle(self, *args, **options):
        certificates = Certificate.objects.filter(pdf_generated=False)
        
        for cert in certificates:
            printer = Printer(
                template_name='certificates/template.html',
                context={'certificate': cert}
            )
            
            pdf_bytes = printer.write_pdf()
            
            # Save or send via email
            cert.pdf_data = pdf_bytes
            cert.pdf_generated = True
            cert.save()
            
            self.stdout.write(f"Generated certificate {cert.id}")
```

### 3. Helper Utilities

#### get_stylesheet_path() and get_stylesheets()

Production-ready helpers for resolving CSS file paths.

```python
# utils.py or helpers.py
from oxutils.pdf.utils import get_stylesheet_path, get_stylesheets

# Get single stylesheet path
css_path = get_stylesheet_path('css/invoice.css')

# Get multiple stylesheets
stylesheets = get_stylesheets('css/base.css', 'css/invoice.css')
```

**How it works:**
- In development (`DEBUG=True`): Uses `find()` to locate files in source directories
- In production (`DEBUG=False`): Uses `STATIC_ROOT` where `collectstatic` copied files
- Returns `None` if file not found
- Handles both scenarios automatically

#### Usage in Views

```python
from oxutils.pdf import Printer
from oxutils.pdf.utils import get_stylesheets

def generate_invoice_pdf(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    
    printer = Printer(
        template_name='invoices/invoice.html',
        context={'invoice': invoice},
        stylesheets=get_stylesheets('css/invoice.css', 'css/print.css')
    )
    
    pdf_bytes = printer.write_pdf()
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.number}.pdf"'
    return response
```

## Template Examples

### Basic PDF Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice #{{ invoice.number }}</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Invoice #{{ invoice.number }}</h1>
        <p>Date: {{ invoice.date }}</p>
    </div>
    
    <div class="content">
        <p>Customer: {{ invoice.customer.name }}</p>
        <p>Total: {{ invoice.total }} USD</p>
    </div>
</body>
</html>
```

### With External CSS

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Report</title>
    <link rel="stylesheet" href="{{ STATIC_URL }}css/pdf_style.css">
</head>
<body>
    <div class="report-header">
        <h1>{{ report.title }}</h1>
    </div>
    
    <div class="report-content">
        {{ report.content|safe }}
    </div>
</body>
</html>
```

### CSS for PDF

```css
/* static/css/pdf_style.css */
@page {
    size: A4;
    margin: 2cm;
    
    @top-center {
        content: "Company Name";
    }
    
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
    }
}

body {
    font-family: 'Helvetica', 'Arial', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

.page-break {
    page-break-after: always;
}

.no-break {
    page-break-inside: avoid;
}

h1 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

table th {
    background-color: #f2f2f2;
}
```

## Configuration

### Settings

```python
# settings.py

# Base URL for resolving static files in PDFs
WEASYPRINT_BASEURL = 'http://127.0.0.1:8000/'  # Development
# WEASYPRINT_BASEURL = 'https://yourdomain.com/'  # Production

# Static files configuration (required)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files configuration (for images in PDFs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### WeasyPrint Options

Available options for `pdf_options`:

```python
pdf_options = {
    'pdf_forms': True,              # Enable PDF forms
    'uncompressed_pdf': False,      # Compress PDF (smaller file)
    'pdf_version': '1.7',           # PDF version
    'pdf_identifier': False,        # Include PDF identifier
    'pdf_variant': 'pdf/a-3b',      # PDF/A variant
    'custom_metadata': {            # Custom metadata
        'Author': 'Your Company',
        'Title': 'Document Title',
    }
}
```

## Production Deployment

### 1. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 2. Update Settings

```python
# settings.py (production)
DEBUG = False
WEASYPRINT_BASEURL = 'https://yourdomain.com/'
STATIC_ROOT = '/var/www/staticfiles/'
```

### 3. Use Helper Functions

Always use `get_stylesheets()` for production compatibility:

```python
from oxutils.pdf.utils import get_stylesheets

stylesheets = get_stylesheets('css/invoice.css')
```

## Advanced Features

### Custom Font Configuration

```python
from oxutils.pdf import Printer
import weasyprint

class CustomPrinter(Printer):
    def get_font_config(self):
        """Custom font configuration"""
        font_config = weasyprint.text.fonts.FontConfiguration()
        # Add custom fonts here
        return font_config
```

### Custom URL Fetcher

The module includes `django_url_fetcher` that handles Django static and media files:

```python
from oxutils.pdf.utils import django_url_fetcher

# Automatically used by Printer and WeasyTemplateView
# Handles file://, STATIC_URL, and MEDIA_URL paths
```

### Multiple Stylesheets

```python
printer = Printer(
    template_name='report.html',
    context=context,
    stylesheets=get_stylesheets(
        'css/base.css',
        'css/report.css',
        'css/print.css'
    )
)
```

## API Reference

### WeasyTemplateView

**Class Attributes:**
- `template_name`: Template to render
- `pdf_filename`: Default filename for download
- `pdf_attachment`: Boolean, force download (True) or inline (False)
- `pdf_stylesheets`: List of CSS file paths
- `pdf_options`: Dict of WeasyPrint options

**Methods:**
- `get_pdf_filename()`: Return dynamic filename
- `get_pdf_stylesheets()`: Return list of stylesheet paths
- `get_pdf_options()`: Return WeasyPrint options dict
- `get_context_data(**kwargs)`: Return template context

### Printer

**Constructor:**
```python
Printer(
    template_name=None,    # Template path
    context=None,          # Template context dict
    stylesheets=None,      # List of CSS paths
    options=None,          # WeasyPrint options dict
    base_url=None          # Base URL override
)
```

**Methods:**
- `render_html(**kwargs)`: Render template to HTML string
- `get_document(**kwargs)`: Get WeasyPrint Document object
- `write_pdf(output=None, **kwargs)`: Generate PDF bytes or write to file
- `write_object(file_obj, **kwargs)`: Write PDF to file object
- `get_context_data(**kwargs)`: Get merged context
- `get_base_url()`: Get base URL for static files
- `get_url_fetcher()`: Get URL fetcher function
- `get_font_config()`: Get font configuration
- `get_css(base_url, url_fetcher, font_config)`: Get CSS objects

## Best Practices

1. **Use Helper Functions**: Always use `get_stylesheets()` for production compatibility
2. **Collect Static Files**: Run `collectstatic` before deploying
3. **Set Base URL**: Configure `WEASYPRINT_BASEURL` correctly for your environment
4. **Optimize CSS**: Use `@page` rules for page layout and headers/footers
5. **Handle Large PDFs**: Use pagination and page breaks for long documents
6. **Cache Templates**: Django's template caching applies to PDF templates
7. **Test in Production Mode**: Test PDF generation with `DEBUG=False` locally
8. **Use BytesIO**: For FileField saving, use `BytesIO` instead of temporary files
9. **Error Handling**: Wrap PDF generation in try/except blocks
10. **Async Generation**: Use Celery for large or slow PDF generation

## Troubleshooting

### CSS Not Loading

**Problem**: Stylesheets not found in production

**Solution**: Use `get_stylesheets()` helper:
```python
from oxutils.pdf.utils import get_stylesheets
stylesheets = get_stylesheets('css/style.css')
```

### Images Not Displaying

**Problem**: Images don't appear in PDF

**Solution**: Use absolute URLs or ensure `WEASYPRINT_BASEURL` is set:
```html
<img src="{{ STATIC_URL }}images/logo.png" alt="Logo">
```

### Font Issues

**Problem**: Fonts not rendering correctly

**Solution**: Use web-safe fonts or configure custom fonts:
```css
body {
    font-family: 'Helvetica', 'Arial', sans-serif;
}
```

### Large File Sizes

**Problem**: PDF files are too large

**Solution**: Enable compression:
```python
pdf_options = {'uncompressed_pdf': False}
```

### Slow Generation

**Problem**: PDF generation is slow

**Solution**: Use Celery for async generation:
```python
@shared_task
def generate_pdf_async(doc_id):
    # Generate PDF in background
    pass
```

## Example Project

See the complete example project in `examples/myproject/` for:
- WeasyTemplateView usage
- Standalone Printer usage
- FileField saving with BytesIO
- Production-ready helpers
- Template examples
- CSS styling

## Dependencies

- `weasyprint>=60.0`: PDF generation engine
- `django>=4.2`: Web framework
- `django.contrib.staticfiles`: Static file handling
