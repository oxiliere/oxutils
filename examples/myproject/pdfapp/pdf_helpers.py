import os
from django.conf import settings
from django.contrib.staticfiles.finders import find


def get_stylesheet_path(relative_path):
    if settings.DEBUG:
        path = find(relative_path)
        if path:
            return path
    print('Le DEBUG est False')
    static_root_path = os.path.join(settings.STATIC_ROOT, relative_path)
    if os.path.exists(static_root_path):
        return static_root_path
    
    return None


def get_stylesheets(*relative_paths):
    stylesheets = []
    for path in relative_paths:
        resolved = get_stylesheet_path(path)
        if resolved:
            stylesheets.append(resolved)
    return stylesheets
