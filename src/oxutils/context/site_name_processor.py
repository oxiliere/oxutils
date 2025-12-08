"""
Context processor for site name
"""

def site_name(request):
    from oxutils.settings import oxi_settings

    return {
        'site_name': oxi_settings.site_name,
        'site_domain': oxi_settings.site_domain,
    }
