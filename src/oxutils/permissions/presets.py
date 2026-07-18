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

        # Tag the preset with its originating app label (used for
        # scope-ownership validation and error messages).
        preset["_app_label"] = app_config.label

        presets.append(preset)
        logger.debug(
            "permission_preset_discovered",
            app=app_config.label,
            roles=len(preset.get("roles", [])),
            groups=len(preset.get("groups", [])),
            grants=len(preset.get("role_grants", [])),
        )

    return presets


def _normalize_scope(entry) -> dict:
    """Normalize a scope entry to ``{"key": str, "label": lazy str}``.

    The label is kept as a lazy string when provided — it will be
    resolved at request time when the frontend calls the endpoint.
    """
    if isinstance(entry, str):
        return {"key": entry, "label": entry}
    if isinstance(entry, dict):
        key = entry.get("key", "")
        label = entry.get("label")
        return {"key": str(key), "label": label if label else str(key)}
    return {"key": str(entry), "label": str(entry)}


def discover_access_scopes() -> list[dict]:
    """Walk installed apps and collect their ``ACCESS_SCOPES``.

    Returns a list of normalized scope dicts ``{"key", "label"}``.
    Each entry in ``ACCESS_SCOPES`` can be a plain string (key only)
    or a dict with ``key`` and ``label`` (translatable).
    """
    scopes: list[dict] = []
    seen_keys: set[str] = set()

    for app_config in apps.get_app_configs():
        try:
            mod = importlib.import_module(f"{app_config.name}.permissions")
        except (ModuleNotFoundError, ImportError):
            continue

        app_scopes = getattr(mod, "ACCESS_SCOPES", None)
        if not isinstance(app_scopes, list):
            continue

        for entry in app_scopes:
            normalized = _normalize_scope(entry)
            key = normalized["key"]
            if key and key not in seen_keys:
                seen_keys.add(key)
                scopes.append(normalized)
                logger.debug(
                    "access_scope_discovered",
                    app=app_config.label,
                    scope=key,
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
            logger.debug(
                "access_application_discovered",
                app=app_config.label,
                application=app_name,
            )

    return applications


def register_preset(base_preset: dict) -> dict:
    """Extend *base_preset* with presets discovered from installed apps.

    **Scope ownership** — each scope in ``actions`` is strictly owned by
    the first app that defines it.  If a second app tries to define the
    same scope, ``ImproperlyConfigured`` is raised immediately.
    """
    from django.core.exceptions import ImproperlyConfigured

    base_roles = base_preset.setdefault("roles", [])
    base_groups = base_preset.setdefault("groups", [])
    base_grants = base_preset.setdefault("role_grants", [])
    base_actions = base_preset.setdefault("actions", {})

    # ── track scope ownership ──────────────────────────────────────
    # The base preset (settings.py) owns the scopes it defines.
    scope_owners: dict[str, str] = {}
    for scope in base_actions:
        scope_owners[scope] = "settings.PERMISSION_PRESET"

    for preset in discover_app_presets():
        app_label = preset.get("_app_label", "unknown")

        base_roles.extend(preset.get("roles", []))
        base_groups.extend(preset.get("groups", []))
        base_grants.extend(preset.get("role_grants", []))

        # ── strict scope ownership ───────────────────────────────
        for scope in preset.get("actions", {}):
            if scope in scope_owners:
                raise ImproperlyConfigured(
                    f"Scope '{scope}' is already owned by '{scope_owners[scope]}'. "
                    f"App '{app_label}' cannot redefine it. "
                    f"Each scope must be owned by exactly one app."
                )
            scope_owners[scope] = app_label

            # Copy the scope's action definitions (no merging needed —
            # we already verified there's no conflict).
            base_actions[scope] = dict(preset["actions"][scope])

    return base_preset


def register_access_scopes() -> None:
    """Extend ``settings.ACCESS_SCOPES`` with scopes discovered from apps.

    Merges normalized scope dicts.  If ``settings.ACCESS_SCOPES`` is a list
    of plain strings they are normalized first.  When a scope appears both
    as a plain string and as a dict, the **dict wins** (preserves the label).
    """
    merged: dict[str, dict] = {}

    # Process settings-based scopes first (strings override nothing)
    raw = getattr(settings, "ACCESS_SCOPES", [])
    if isinstance(raw, list):
        for entry in raw:
            norm = _normalize_scope(entry)
            key = norm["key"]
            if key:
                merged.setdefault(key, norm)

    # Discovered scopes (from app permissions.py) may have labels —
    # they override plain-string entries with the same key.
    for scope_dict in discover_access_scopes():
        key = scope_dict["key"]
        if key:
            existing = merged.get(key)
            # Dict wins over plain string (preserves the translatable label)
            if existing is None or ("label" in scope_dict and scope_dict["label"] != key):
                merged[key] = scope_dict

    settings.ACCESS_SCOPES = list(merged.values())
    logger.debug("access_scopes_registered", count=len(merged))


def register_access_applications() -> None:
    """Extend ``settings.ACCESS_APPLICATIONS`` with apps discovered from installed apps."""
    existing = list(getattr(settings, "ACCESS_APPLICATIONS", []))

    for app_name in discover_access_applications():
        if app_name not in existing:
            existing.append(app_name)

    settings.ACCESS_APPLICATIONS = existing
    logger.debug("access_applications_registered", count=len(existing))
