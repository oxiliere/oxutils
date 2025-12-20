from django.conf import settings




_SETTINGS = {
    'BUILD_ABSOLUTE_URI_CALLABLE': None, # for building absolute URIs used by weasyprint for PDF generation
}

BUILD_ABSOLUTE_URI_CALLABLE = _SETTINGS.get('BUILD_ABSOLUTE_URI_CALLABLE')
