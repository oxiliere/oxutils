"""
Permission preset auto-discovery.

Walk installed apps, collect their ``PERMISSION_PRESET`` dicts,
``ACCESS_APPLICATION_NAME`` and ``ACCESS_SCOPES``, and merge them
into the global configuration.

Called from ``PermissionsConfig.ready()`` when the app registry is ready.
"""

import importlib

import structlog
from django.apps import apps
from django.conf import settings

logger = structlog.get_logger(__name__)


def discover_app_presets() -> list[dict]:
    """Walk installed apps and collect their ``PERMISSION_PRESET``."""
    presets: list[dict] = []
    for app_config in apps.get_app_configs():
        try:
            mod = importlib.import_module(f"{app_config.name}.permissions")
        except (ModuleNotFoundError, ImportError):
            continue

        preset = getattr(mod, "PERMISSION_PRESET", None)
        if not isinstance(preset, dict):
            continue

        for role in preset.get("roles", []):
            role.setdefault("app", app_config.label)
        for group in preset.get("groups", []):
            group.setdefault("app", app_config.label)
        for grant in preset.get("role_grants", []):
            grant.setdefault("app", app_config.label)

        presets.append(preset)
        logger.info(
            "permission_preset_discovered",
            app=app_config.label,
            roles=len(preset.get("roles", [])),
            groups=len(preset.get("groups", [])),
            grants=len(preset.get("role_grants", [])),
        )

    return presets


def discover_access_scopes() -> list[str]:
    """Walk installed apps and collect their ``ACCESS_SCOPES``."""
    scopes: list[str] = []
    for app_config in apps.get_app_configs():
        try:
            mod = importlib.import_module(f"{app_config.name}.permissions")
        except (ModuleNotFoundError, ImportError):
            continue

        app_scopes = getattr(mod, "ACCESS_SCOPES", None)
        if isinstance(app_scopes, list):
            for scope in app_scopes:
                if scope not in scopes:
                    scopes.append(scope)
                    logger.info(
                        "access_scope_discovered",
                        app=app_config.label,
                        scope=scope,
                    )

    return scopes


def discover_access_applications() -> list[str]:
    """Walk installed apps and collect their ``ACCESS_APPLICATION_NAME``."""
    applications: list[str] = []
    for app_config in apps.get_app_configs():
        try:
            mod = importlib.import_module(f"{app_config.name}.permissions")
        except (ModuleNotFoundError, ImportError):
            continue

        app_name = getattr(mod, "ACCESS_APPLICATION_NAME", None)
        if isinstance(app_name, str) and app_name not in applications:
            applications.append(app_name)
            logger.info(
                "access_application_discovered",
                app=app_config.label,
                application=app_name,
            )

    return applications


def register_preset(base_preset: dict) -> dict:
    """Extend *base_preset* with presets discovered from installed apps."""
    base_roles = base_preset.setdefault("roles", [])
    base_groups = base_preset.setdefault("groups", [])
    base_grants = base_preset.setdefault("role_grants", [])

    for preset in discover_app_presets():
        base_roles.extend(preset.get("roles", []))
        base_groups.extend(preset.get("groups", []))
        base_grants.extend(preset.get("role_grants", []))

    return base_preset


def register_access_scopes() -> None:
    """Extend ``settings.ACCESS_SCOPES`` with scopes discovered from installed apps."""
    existing = list(getattr(settings, "ACCESS_SCOPES", []))

    for scope in discover_access_scopes():
        if scope not in existing:
            existing.append(scope)

    settings.ACCESS_SCOPES = existing
    logger.info("access_scopes_registered", count=len(existing))


def register_access_applications() -> None:
    """Extend ``settings.ACCESS_APPLICATIONS`` with apps discovered from installed apps."""
    existing = list(getattr(settings, "ACCESS_APPLICATIONS", []))

    for app_name in discover_access_applications():
        if app_name not in existing:
            existing.append(app_name)

    settings.ACCESS_APPLICATIONS = existing
    logger.info("access_applications_registered", count=len(existing))
