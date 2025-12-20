import logging, io

from bs4 import BeautifulSoup
from django.template.response import TemplateResponse
from django.utils.module_loading import import_string
import weasyprint

from .. import settings


LOGGER = logging.getLogger(__name__)


class PdfTemplateResponse(TemplateResponse):
    """
    Response as PDF content.
    """

    def __init__(self, request, template, context=None, content_type=None,
                 status=None, **kwargs):
        super(PdfTemplateResponse, self).__init__(request, template,
            context=context, content_type='application/pdf', status=status,
            **kwargs)

    @property
    def rendered_content(self):
        """
        Converts the HTML content generated from the template
        as a Pdf document on the fly.
        """
        # TODO: make this a function
        html_content = super(PdfTemplateResponse, self).rendered_content
        soup = BeautifulSoup(html_content.encode('utf-8'), 'html.parser')
        for lnk in soup.find_all('a'):
            href = lnk.get('href')
            if href and href.startswith('/'):
                lnk['href'] = build_absolute_uri(
                    location=href, request=self._request)
        html_content = soup.prettify()
        cstr = io.BytesIO()

        doc = weasyprint.HTML(string=html_content, base_url=build_absolute_uri(
                    location='/', request=self._request))
        doc.write_pdf(cstr)

        return cstr.getvalue()


class PdfTemplateError(Exception):
    pass


# TODO: add BUILD_ABSOLUTE_URI_CALLABLE
def build_absolute_uri(location='/', request=None, site=None,
                       with_scheme=True, force_subdomain=False):
    if settings.BUILD_ABSOLUTE_URI_CALLABLE:
        try:
            return import_string(
                settings.BUILD_ABSOLUTE_URI_CALLABLE)(location=location,
                    request=request, site=site,
                    with_scheme=with_scheme, force_subdomain=force_subdomain)
        except ImportError:
            pass
    if request:
        return request.build_absolute_uri(location)

    return location
