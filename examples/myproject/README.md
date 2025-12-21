# Django PDF Example Project

This is a complete Django example project demonstrating the usage of `oxutils.pdf` package, specifically the `Printer` class and `WeasyTemplateView`.

## Features Demonstrated

1. **WeasyTemplateView** - Class-based view for PDF generation
2. **Printer (standalone)** - Independent PDF generation without views
3. **File saving** - Saving generated PDFs to Django FileField
4. **Multiple use cases**:
   - Direct PDF download in browser
   - PDF generation and storage
   - View-based PDF rendering

## Installation

### Prerequisites

- Python 3.9+
- uv package manager

### Setup

1. Navigate to the project directory:
```bash
cd examples/myproject
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Run migrations:
```bash
uv run python manage.py migrate
```

4. Create a superuser:
```bash
uv run python manage.py createsuperuser
```

5. Collect static files:
```bash
uv run python manage.py collectstatic --noinput
```

6. Run the development server:
```bash
uv run python manage.py runserver
```

## Usage

### 1. Create Profiles

Visit http://127.0.0.1:8000/admin/ and create some Profile objects with:
- Name
- Email
- Bio

### 2. View Profiles

Visit http://127.0.0.1:8000/ to see the list of profiles.

### 3. Generate PDFs

For each profile, you can:

- **View as PDF (WeasyTemplateView)**: Uses the class-based view approach
  - URL: `/profile/<id>/pdf/`
  - Demonstrates: `WeasyTemplateView` usage

- **Download PDF (Printer)**: Uses the standalone Printer class
  - URL: `/profile/<id>/download-pdf/`
  - Demonstrates: `Printer` class with direct bytes return

- **Generate & Save CV**: Generates PDF and saves to FileField
  - URL: `/profile/<id>/generate-cv/`
  - Demonstrates: `Printer` class with file saving using `io.BytesIO()`

## Code Examples

### Using WeasyTemplateView (Class-Based View)

```python
from oxutils.pdf import WeasyTemplateView

class ProfilePDFView(WeasyTemplateView):
    template_name = 'pdfapp/profile_pdf.html'
    pdf_stylesheets = ['css/pdf_style.css']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        context['profile'] = profile
        return context

    def get_pdf_filename(self):
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return f'cv_{profile.name.replace(" ", "_")}.pdf'
```

### Using Printer (Standalone)

#### Direct Download
```python
from oxutils.pdf import Printer

def download_standalone_pdf(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    
    printer = Printer(
        template_name='pdfapp/profile_pdf.html',
        context={'profile': profile},
        stylesheets=['css/pdf_style.css'],
    )
    
    pdf_bytes = printer.write_pdf()
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cv.pdf"'
    
    return response
```

#### Save to FileField
```python
import io
from django.core.files.base import ContentFile
from oxutils.pdf import Printer

def generate_and_save_cv(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    
    # Create printer instance
    printer = Printer(
        template_name='pdfapp/profile_pdf.html',
        context={'profile': profile},
        stylesheets=['css/pdf_style.css'],
    )
    
    # Generate PDF to BytesIO
    obj = io.BytesIO()
    printer.write_pdf(output=obj)
    
    # Save to FileField
    filename = f'cv_{profile.name.replace(" ", "_")}.pdf'
    profile.curriculum_vitae.save(filename, ContentFile(obj.getvalue()), save=True)
    
    return HttpResponse(f'CV generated and saved for {profile.name}')
```

### Using Printer in Management Commands or Celery Tasks

```python
from oxutils.pdf import Printer

# In a management command or Celery task
printer = Printer(
    template_name='my_template.html',
    context={'data': 'value'},
    stylesheets=['style.css'],
    base_url='http://example.com'
)

# Option 1: Get bytes
pdf_bytes = printer.write_pdf()

# Option 2: Write to file object
with open('output.pdf', 'wb') as f:
    printer.write_object(f)

# Option 3: Write to BytesIO
import io
obj = io.BytesIO()
printer.write_pdf(output=obj)
```

## Project Structure

```
myproject/
├── manage.py
├── pyproject.toml
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── pdfapp/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── static/
    │   └── css/
    │       └── pdf_style.css
    └── templates/
        └── pdfapp/
            ├── profile_list.html
            ├── profile_detail.html
            └── profile_pdf.html
```

## Key Concepts

### Printer vs WeasyTemplateView

- **WeasyTemplateView**: Best for Django views that return PDF responses
- **Printer**: Best for standalone PDF generation (tasks, commands, scripts)

### Customization

Both approaches support:
- Custom stylesheets via `pdf_stylesheets` or `stylesheets` parameter
- WeasyPrint options via `pdf_options` or `options` parameter
- Base URL configuration via `WEASYPRINT_BASEURL` setting or `base_url` parameter
- Font configuration via `get_font_config()` method

## Dependencies

- Django >= 4.2
- WeasyPrint >= 60.0
- oxutils (parent package)

## Notes

- The `WEASYPRINT_BASEURL` setting in `settings.py` helps WeasyPrint resolve static files
- CSS files are loaded from the static directory
- The django_url_fetcher handles Django static and media files correctly
