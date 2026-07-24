"""
Domain-oriented actions defined via PERMISSION_PRESET["actions"].

Each scope has its own set of named actions with optional hierarchy
(via ``implies``).  Actions are no longer hard-coded single letters;
the developer defines them per scope (or globally) in the preset.

Example preset::

    PERMISSION_PRESET = {
        "actions": {
            "orders": {
                "create": {"implies": []},
                "approve": {"implies": ["create"]},
                "cancel": {"implies": []},
                "refund": {"implies": ["approve"]},
            },
            "articles": {
                "read": {"implies": []},
                "write": {"implies": ["read"]},
                "publish": {"implies": ["write"]},
                "archive": {"implies": ["publish"]},
            },
        },
        "roles": [...],
        "groups": [...],
        "role_grants": [...],
    }

If a scope is not declared in ``actions``, an empty dict is returned and
no hierarchy expansion occurs (actions are treated as independent).
"""

from __future__ import annotations


def _get_all_actions() -> dict[str, dict[str, dict]]:
    """Return all action definitions from ``PERMISSION_PRESET["actions"]``."""
    from django.conf import settings

    preset = getattr(settings, "PERMISSION_PRESET", {})
    actions = preset.get("actions", {})
    if not isinstance(actions, dict):
        return {}
    return actions


def get_actions_for_scope(scope: str) -> dict[str, dict]:
    """Return the action definitions for a given *scope*.

    Returns:
        Dict mapping action name → definition (currently only ``implies`` key).
    """
    return _get_all_actions().get(scope, {})


def get_valid_actions(scope: str) -> list[str]:
    """Return the list of valid action names for *scope*."""
    return list(get_actions_for_scope(scope).keys())


def get_all_valid_actions() -> set[str]:
    """Return the union of all action names across all scopes."""
    all_actions: set[str] = set()
    for scope_actions in _get_all_actions().values():
        all_actions.update(scope_actions.keys())
    return all_actions


def get_implied_actions(scope: str, action: str) -> set[str]:
    """Return actions that *action* implies on *scope*."""
    actions_for_scope = get_actions_for_scope(scope)
    action_def = actions_for_scope.get(action, {})
    implies = action_def.get("implies", [])
    return set(implies) if isinstance(implies, list) else set()


def expand_actions(scope: str, actions: list[str]) -> list[str]:
    """Recursively expand *actions* to include everything they imply.

    Example::

        >>> # If "approve" implies "create":
        >>> expand_actions("orders", ["approve"])
        ["approve", "create"]
    """
    expanded: set[str] = set(actions)
    stack: list[str] = list(actions)

    while stack:
        action = stack.pop()
        for implied in get_implied_actions(scope, action):
            if implied not in expanded:
                expanded.add(implied)
                stack.append(implied)

    return sorted(expanded)


def collapse_actions(scope: str, actions: list[str]) -> set[str]:
    """Remove implied actions, keeping only the most-specific (root) actions.

    Example::

        >>> # If "approve" implies "create":
        >>> collapse_actions("orders", ["approve", "create"])
        {"approve"}
    """
    root = set(actions)
    for action in list(root):
        implied = get_implied_actions(scope, action)
        root -= implied
    return root


def validate_actions_for_scope(scope: str, actions: list[str]) -> list[str]:
    """Validate that *actions* are declared for *scope*.

    Returns *actions* unchanged if valid.

    Raises:
        ValueError: if one or more actions are not valid for the scope.
    """
    valid = get_valid_actions(scope)

    # If the scope has no explicit actions defined, allow anything
    # (the developer may rely on implicit validation or global presets).
    if not valid:
        return actions

    invalid = [a for a in actions if a not in valid]
    if invalid:
        raise ValueError(f"Invalid actions for scope '{scope}': {invalid}. Valid actions: {valid}")
    return actions


def get_action_label(scope: str, action: str) -> str:
    """Return the human-readable (translated) label for *action* on *scope*.

    Falls back to the action key itself if no ``label`` is defined.

    Example preset::

        PERMISSION_PRESET = {
            "actions": {
                "orders": {
                    "create": {
                        "implies": [],
                        "label": _("Create"),
                    },
                },
            },
        }

    Usage::

        >>> get_action_label("orders", "create")
        "Créer"  # or "Create" depending on active language
    """
    action_def = get_actions_for_scope(scope).get(action, {})
    label = action_def.get("label")
    if label is not None:
        return str(label)  # force evaluation of lazy translations
    return str(action)


def get_scope_actions_labels(scope: str) -> dict[str, str]:
    """Return all action → label mappings for a scope.

    Returns:
        Dict mapping action key → translated label.
    """
    return {action: get_action_label(scope, action) for action in get_valid_actions(scope)}
