import weasyprint
from django.conf import settings
from django.template.loader import render_to_string

from oxutils.pdf.utils import django_url_fetcher


class Printer:
    template_name = None
    pdf_stylesheets = []
    pdf_options = {}

    def __init__(self, template_name=None, context=None, stylesheets=None, options=None, base_url=None):
        self.template_name = template_name or self.template_name
        self.context = context or {}
        self._stylesheets = stylesheets or self.pdf_stylesheets
        self._options = options.copy() if options else self.pdf_options.copy()
        self._base_url = base_url

    def get_context_data(self, **kwargs):
        context = self.context.copy()
        context.update(kwargs)
        return context

    def get_pdf_filename(self):
        return None

    def get_base_url(self):
        if self._base_url:
            return self._base_url
        return getattr(settings, 'WEASYPRINT_BASEURL', '/')

    def get_url_fetcher(self):
        return django_url_fetcher

    def get_font_config(self):
        return weasyprint.text.fonts.FontConfiguration()

    def get_css(self, base_url, url_fetcher, font_config):
        return [
            weasyprint.CSS(
                value,
                base_url=base_url,
                url_fetcher=url_fetcher,
                font_config=font_config,
            )
            for value in self._stylesheets
        ]

    def render_html(self, **kwargs):
        context = self.get_context_data(**kwargs)
        return render_to_string(self.template_name, context)

    def get_document(self, **kwargs):
        base_url = self.get_base_url()
        url_fetcher = self.get_url_fetcher()
        font_config = self.get_font_config()

        html_content = self.render_html(**kwargs)
        html = weasyprint.HTML(
            string=html_content,
            base_url=base_url,
            url_fetcher=url_fetcher,
        )

        self._options.setdefault(
            'stylesheets',
            self.get_css(base_url, url_fetcher, font_config),
        )

        return html.render(
            font_config=font_config,
            **self._options,
        )

    def write_pdf(self, output=None, **kwargs):
        document = self.get_document(**kwargs)
        return document.write_pdf(target=output, **self._options)

    def write_object(self, file_obj, **kwargs):
        return self.write_pdf(output=file_obj, **kwargs)
