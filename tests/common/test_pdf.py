"""
Tests for PDF generation module.
"""
import io
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.template import Template, Context
from django.core.files.base import ContentFile
import weasyprint


@pytest.mark.django_db
class TestPrinter(TestCase):
    """Tests for the Printer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.template_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test PDF</title></head>
        <body><h1>{{ title }}</h1><p>{{ content }}</p></body>
        </html>
        """
        self.context = {
            'title': 'Test Document',
            'content': 'This is test content.'
        }

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    def test_printer_initialization(self, mock_html, mock_render):
        """Test Printer initialization with parameters."""
        from oxutils.pdf.printer import Printer
        
        printer = Printer(
            template_name='test.html',
            context={'key': 'value'},
            stylesheets=['style.css'],
            options={'pdf_forms': True},
            base_url='http://example.com'
        )
        
        assert printer.template_name == 'test.html'
        assert printer.context == {'key': 'value'}
        assert printer._stylesheets == ['style.css']
        assert printer._options == {'pdf_forms': True}
        assert printer._base_url == 'http://example.com'

    @patch('oxutils.pdf.printer.render_to_string')
    def test_render_html(self, mock_render):
        """Test HTML rendering from template."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>Test</body></html>'
        
        printer = Printer(
            template_name='test.html',
            context={'title': 'Test'}
        )
        
        html = printer.render_html()
        
        mock_render.assert_called_once_with('test.html', {'title': 'Test'})
        assert html == '<html><body>Test</body></html>'

    @patch('oxutils.pdf.printer.render_to_string')
    def test_get_context_data(self, mock_render):
        """Test context data merging."""
        from oxutils.pdf.printer import Printer
        
        printer = Printer(
            template_name='test.html',
            context={'base': 'value'}
        )
        
        context = printer.get_context_data(extra='data')
        
        assert context == {'base': 'value', 'extra': 'data'}

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_get_document(self, mock_font_config, mock_html, mock_render):
        """Test document generation."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(template_name='test.html')
        document = printer.get_document()
        
        mock_html.assert_called_once()
        mock_html_instance.render.assert_called_once()
        assert document == mock_document

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_write_pdf_returns_bytes(self, mock_font_config, mock_html, mock_render):
        """Test PDF generation returns bytes."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_document.write_pdf.return_value = b'PDF_CONTENT'
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(template_name='test.html')
        pdf_bytes = printer.write_pdf()
        
        assert pdf_bytes == b'PDF_CONTENT'
        mock_document.write_pdf.assert_called_once()

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_write_pdf_to_file_object(self, mock_font_config, mock_html, mock_render):
        """Test PDF writing to file object."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_document.write_pdf.return_value = b'PDF_CONTENT'
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(template_name='test.html')
        
        output = io.BytesIO()
        result = printer.write_pdf(output=output)
        
        mock_document.write_pdf.assert_called_once()
        assert result == b'PDF_CONTENT'

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_write_object(self, mock_font_config, mock_html, mock_render):
        """Test write_object method."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_document.write_pdf.return_value = b'PDF_CONTENT'
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(template_name='test.html')
        
        file_obj = io.BytesIO()
        result = printer.write_object(file_obj)
        
        assert result == b'PDF_CONTENT'

    @override_settings(WEASYPRINT_BASEURL='http://test.com/')
    @patch('oxutils.pdf.printer.render_to_string')
    def test_get_base_url_from_settings(self, mock_render):
        """Test base URL retrieval from settings."""
        from oxutils.pdf.printer import Printer
        
        printer = Printer(template_name='test.html')
        base_url = printer.get_base_url()
        
        assert base_url == 'http://test.com/'

    @patch('oxutils.pdf.printer.render_to_string')
    def test_get_base_url_override(self, mock_render):
        """Test base URL override in constructor."""
        from oxutils.pdf.printer import Printer
        
        printer = Printer(
            template_name='test.html',
            base_url='http://custom.com/'
        )
        base_url = printer.get_base_url()
        
        assert base_url == 'http://custom.com/'

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.CSS')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_get_css_with_stylesheets(self, mock_font_config, mock_css, mock_render):
        """Test CSS loading with stylesheets."""
        from oxutils.pdf.printer import Printer
        
        printer = Printer(
            template_name='test.html',
            stylesheets=['style1.css', 'style2.css']
        )
        
        mock_font = MagicMock()
        css_list = printer.get_css('http://base.com', lambda x: x, mock_font)
        
        assert len(css_list) == 2
        assert mock_css.call_count == 2


@pytest.mark.django_db
class TestWeasyTemplateView(TestCase):
    """Tests for WeasyTemplateView class."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    @patch('oxutils.pdf.views.weasyprint.HTML')
    @patch('oxutils.pdf.views.weasyprint.text.fonts.FontConfiguration')
    def test_weasy_template_view_get(self, mock_font_config, mock_html):
        """Test WeasyTemplateView GET request."""
        from oxutils.pdf.views import WeasyTemplateView
        
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_document.write_pdf.return_value = b'PDF_CONTENT'
        mock_html_instance.render.return_value = mock_document
        
        class TestPDFView(WeasyTemplateView):
            template_name = 'test.html'
            pdf_filename = 'test.pdf'
            
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context['title'] = 'Test'
                return context
        
        request = self.factory.get('/test/')
        view = TestPDFView.as_view()
        response = view(request)
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'test.pdf' in response['Content-Disposition']

    def test_get_pdf_filename(self):
        """Test get_pdf_filename method."""
        from oxutils.pdf.views import WeasyTemplateView
        
        class TestPDFView(WeasyTemplateView):
            template_name = 'test.html'
            pdf_filename = 'document.pdf'
        
        view = TestPDFView()
        filename = view.get_pdf_filename()
        
        assert filename == 'document.pdf'

    def test_get_pdf_stylesheets(self):
        """Test get_pdf_stylesheets method."""
        from oxutils.pdf.views import WeasyTemplateView
        
        class TestPDFView(WeasyTemplateView):
            template_name = 'test.html'
            pdf_stylesheets = ['style1.css', 'style2.css']
        
        view = TestPDFView()
        stylesheets = view.get_pdf_stylesheets()
        
        assert stylesheets == ['style1.css', 'style2.css']

    def test_get_pdf_options(self):
        """Test get_pdf_options method."""
        from oxutils.pdf.views import WeasyTemplateView
        
        class TestPDFView(WeasyTemplateView):
            template_name = 'test.html'
            pdf_options = {'pdf_forms': True, 'uncompressed_pdf': False}
        
        view = TestPDFView()
        options = view.get_pdf_options()
        
        assert options == {'pdf_forms': True, 'uncompressed_pdf': False}


@pytest.mark.django_db
class TestPDFUtils(TestCase):
    """Tests for PDF utility functions."""

    @override_settings(DEBUG=True)
    @patch('oxutils.pdf.utils.find')
    def test_get_stylesheet_path_debug_mode(self, mock_find):
        """Test stylesheet path resolution in DEBUG mode."""
        from oxutils.pdf.utils import get_stylesheet_path
        
        mock_find.return_value = '/path/to/static/css/style.css'
        
        path = get_stylesheet_path('css/style.css')
        
        mock_find.assert_called_once_with('css/style.css')
        assert path == '/path/to/static/css/style.css'

    @override_settings(DEBUG=False, STATIC_ROOT='/var/www/static/')
    @patch('oxutils.pdf.utils.os.path.exists')
    def test_get_stylesheet_path_production_mode(self, mock_exists):
        """Test stylesheet path resolution in production mode."""
        from oxutils.pdf.utils import get_stylesheet_path
        
        mock_exists.return_value = True
        
        path = get_stylesheet_path('css/style.css')
        
        assert path == '/var/www/static/css/style.css'
        mock_exists.assert_called_once_with('/var/www/static/css/style.css')

    @override_settings(DEBUG=False, STATIC_ROOT='/var/www/static/')
    @patch('oxutils.pdf.utils.os.path.exists')
    def test_get_stylesheet_path_not_found(self, mock_exists):
        """Test stylesheet path when file doesn't exist."""
        from oxutils.pdf.utils import get_stylesheet_path
        
        mock_exists.return_value = False
        
        path = get_stylesheet_path('css/missing.css')
        
        assert path is None

    @override_settings(DEBUG=True, STATIC_ROOT='/var/www/static/')
    @patch('oxutils.pdf.utils.find')
    def test_get_stylesheets_multiple(self, mock_find):
        """Test getting multiple stylesheets."""
        from oxutils.pdf.utils import get_stylesheets
        
        mock_find.side_effect = [
            '/path/to/style1.css',
            '/path/to/style2.css',
            None  # Third stylesheet not found
        ]
        
        stylesheets = get_stylesheets('style1.css', 'style2.css', 'missing.css')
        
        assert len(stylesheets) == 2
        assert '/path/to/style1.css' in stylesheets
        assert '/path/to/style2.css' in stylesheets

    @override_settings(DEBUG=True, STATIC_ROOT='/var/www/static/')
    @patch('oxutils.pdf.utils.find')
    def test_get_stylesheets_empty(self, mock_find):
        """Test getting stylesheets when none exist."""
        from oxutils.pdf.utils import get_stylesheets
        
        mock_find.return_value = None
        
        stylesheets = get_stylesheets('missing1.css', 'missing2.css')
        
        assert len(stylesheets) == 0


@pytest.mark.django_db
class TestDjangoURLFetcher(TestCase):
    """Tests for django_url_fetcher utility."""

    @override_settings(STATIC_URL='/static/', DEBUG=True)
    @patch('oxutils.pdf.utils.find')
    @patch('builtins.open', new_callable=mock_open, read_data=b'CSS_CONTENT')
    def test_fetch_static_file(self, mock_file, mock_find):
        """Test fetching a static file."""
        from oxutils.pdf.utils import django_url_fetcher
        
        mock_find.return_value = '/path/to/static/css/style.css'
        
        result = django_url_fetcher('file:///static/css/style.css')
        
        assert result['mime_type'] == 'text/css'
        assert result['filename'] == 'style.css'
        mock_find.assert_called_once()

    @override_settings(MEDIA_URL='/media/', MEDIA_ROOT='/var/www/media/')
    @patch('oxutils.pdf.utils.default_storage.open')
    def test_fetch_media_file(self, mock_storage_open):
        """Test fetching a media file."""
        from oxutils.pdf.utils import django_url_fetcher
        
        mock_file = MagicMock()
        mock_storage_open.return_value = mock_file
        
        result = django_url_fetcher('file:///media/images/logo.png')
        
        assert result['mime_type'] == 'image/png'
        assert result['filename'] == 'logo.png'
        mock_storage_open.assert_called_once()

    @patch('oxutils.pdf.utils.weasyprint.default_url_fetcher')
    def test_fetch_http_url_fallback(self, mock_default_fetcher):
        """Test fallback to weasyprint default fetcher for HTTP URLs."""
        from oxutils.pdf.utils import django_url_fetcher
        
        mock_default_fetcher.return_value = {'data': 'content'}
        
        result = django_url_fetcher('https://example.com/style.css')
        
        mock_default_fetcher.assert_called_once_with('https://example.com/style.css')
        assert result == {'data': 'content'}


@pytest.mark.django_db
class TestPDFIntegration(TestCase):
    """Integration tests for PDF generation."""

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_full_pdf_generation_workflow(self, mock_font_config, mock_html, mock_render):
        """Test complete PDF generation workflow."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body><h1>Invoice</h1></body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        mock_document.write_pdf.return_value = b'PDF_BYTES'
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(
            template_name='invoice.html',
            context={'invoice_number': '12345'},
            stylesheets=[],
            options={'pdf_forms': False}
        )
        
        pdf_bytes = printer.write_pdf()
        
        assert pdf_bytes == b'PDF_BYTES'
        mock_render.assert_called_once()
        mock_html.assert_called_once()

    @patch('oxutils.pdf.printer.render_to_string')
    @patch('oxutils.pdf.printer.weasyprint.HTML')
    @patch('oxutils.pdf.printer.weasyprint.text.fonts.FontConfiguration')
    def test_pdf_to_bytesio_for_filefield(self, mock_font_config, mock_html, mock_render):
        """Test PDF generation to BytesIO for Django FileField."""
        from oxutils.pdf.printer import Printer
        
        mock_render.return_value = '<html><body>CV</body></html>'
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_document = MagicMock()
        
        # Mock write_pdf to write to the output stream
        def mock_write_pdf(target=None, **kwargs):
            if target is not None:
                target.write(b'CV_PDF_CONTENT')
            return b'CV_PDF_CONTENT'
        
        mock_document.write_pdf = mock_write_pdf
        mock_html_instance.render.return_value = mock_document
        
        printer = Printer(
            template_name='cv.html',
            context={'name': 'John Doe'}
        )
        
        obj = io.BytesIO()
        printer.write_pdf(output=obj)
        
        obj.seek(0)
        content = obj.read()
        
        assert content == b'CV_PDF_CONTENT'
