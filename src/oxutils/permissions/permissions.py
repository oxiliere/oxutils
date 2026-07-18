"""
Permission preset for the built-in ``access`` scope.

This module is **auto-discovered** by ``PermissionsConfig.ready()``
at Django startup.  It defines the named actions used internally by
the permission management endpoints (e.g. ``/api/access/``).

Labels use ``gettext_lazy`` so the frontend can display action names
in the active language.
"""

from django.utils.translation import gettext_lazy as _

# ── Actions used internally by the permissions module ────────────────
# The ``access`` scope is strictly owned by ``oxutils.permissions``.
PERMISSION_PRESET = {
    "actions": {
        "access": {
            "read": {
                "implies": [],
                "label": _("Read"),
            },
            "write": {
                "implies": ["read"],
                "label": _("Write"),
            },
            "update": {
                "implies": ["read"],
                "label": _("Update"),
            },
            "delete": {
                "implies": ["read", "write"],
                "label": _("Delete"),
            },
        },
    },
    "roles": [],
    "groups": [],
    "role_grants": [],
}

# Scopes used by this module (with translatable labels)
ACCESS_SCOPES = [
    {"key": "access", "label": _("Access Management")},
]
