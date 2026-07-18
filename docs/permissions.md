# Permissions System — v0.5.0

**Domain-oriented role-based access control with named actions, groups and custom grants**

> ⚠️ **Breaking change from 0.4.x** — actions are now **named strings** (e.g. `create`, `approve`)
> instead of single letters (`r`, `w`, `d`). The permission string format uses `/` (AND)
> and `|` (OR) separators. See [Migration from 0.4.x](#migration-from-04x) below.

## Features

- **Named actions** — domain-oriented: `create`, `approve`, `cancel`, `publish`…
- **Translatable labels** — each action has a `label` field for i18n frontend display
- **Action hierarchy** — `approve` can imply `create`; declared in the preset via `implies`
- **AND / OR operators** — `/` = all actions required, `|` = at least one
- **Strict scope ownership** — each scope belongs to exactly one app
- Role-based permissions, groups, custom grant overrides, activate/deactivate
- Auto-discovery from app `permissions.py` modules
- Context-based filtering (multi-tenant ready)
- Full traceability with `created_by` and `locked` flags

## Setup

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'oxutils.permissions',
]
```

```bash
python manage.py migrate permissions
```

## Core Concepts

### Action Definitions (NEW in 0.5.0)

Actions are **named strings** with optional **translatable labels** and **hierarchy**,
defined per scope in `PERMISSION_PRESET["actions"]`:

```python
from django.utils.translation import gettext_lazy as _

PERMISSION_PRESET = {
    "actions": {
        "orders": {
            "create":  {"implies": [],               "label": _("Create")},
            "approve": {"implies": ["create"],        "label": _("Approve")},
            "cancel":  {"implies": [],               "label": _("Cancel")},
            "refund":  {"implies": ["approve"],       "label": _("Refund")},
            "read":    {"implies": [],               "label": _("Read")},
        },
        "articles": {
            "read":    {"implies": [],               "label": _("Read")},
            "write":   {"implies": ["read"],          "label": _("Write")},
            "publish": {"implies": ["write"],         "label": _("Publish")},
            "archive": {"implies": ["publish"],       "label": _("Archive")},
        },
    },
    "roles": [...],
    "groups": [...],
    "role_grants": [...],
}
```

- **`implies`** — actions automatically granted when this action is assigned.
  `approve` implies `create` → granting `["approve"]` stores `["approve", "create"]`.
- **`label`** — translated display name for the frontend. Use `gettext_lazy` (`_()`)
  for i18n. Falls back to the action key if omitted.
- **Scope ownership** — each scope is strictly owned by one app. Two apps defining
  the same scope raises `ImproperlyConfigured`.

### Architecture

```
User ──> UserGroup ──> Group ──> Role ──> RoleGrant
  │                                          │
  └──────────> Grant <────────────────────────┘
```

### Models Summary

| Model | Description |
|---|---|
| **Role** | Named permission set (`admin`, `editor`). Optional `app` namespace. |
| **Group** | Collection of roles for bulk assignment (`staff`). |
| **RoleGrant** | Template: which actions a role has on a scope. Actions are expanded via hierarchy. |
| **Grant** | Effective user permission. `locked=False` = inherited, `locked=True` = custom. `is_active` toggle. |
| **UserGroup** | Links user to group for traceability. |

## Configuration

```python
# settings.py

ACCESS_MANAGER_SCOPE = "access"    # optional, defaults to "access"
ACCESS_MANAGER_GROUP = "manager"   # or None
ACCESS_MANAGER_ROLE = "manager"     # or None
ACCESS_MANAGER_CONTEXT = {}

# Scopes — strings (key only) or dicts with translatable labels
from django.utils.translation import gettext_lazy as _

ACCESS_SCOPES = [
    "articles",                                    # plain string → label = key
    "users",
    {"key": "orders",   "label": _("Orders")},      # dict → translatable label
    {"key": "invoices", "label": _("Invoices")},
]

CACHE_CHECK_PERMISSION = False
```

> 💡 **Recommendation**: always use the dict format with `_()` labels for scopes
> visible in the frontend.  The `GET /api/access/scopes` endpoint returns
> `{"key": "...", "label": "..."}` pairs that can be displayed directly.

### Full PERMISSION_PRESET Example

```python
from django.utils.translation import gettext_lazy as _

PERMISSION_PRESET = {
    "actions": {
        "access": {
            "read":   {"implies": [],                  "label": _("Read")},
            "write":  {"implies": ["read"],             "label": _("Write")},
            "delete": {"implies": ["read", "write"],    "label": _("Delete")},
            "update": {"implies": ["read"],             "label": _("Update")},
        },
        "orders": {
            "create":  {"implies": [],                  "label": _("Create")},
            "approve": {"implies": ["create"],          "label": _("Approve")},
            "cancel":  {"implies": [],                  "label": _("Cancel")},
            "read":    {"implies": [],                  "label": _("Read")},
        },
    },
    "roles": [
        {"name": "Manager", "slug": "manager"},
        {"name": "Editor",  "slug": "editor"},
        {"name": "Viewer",  "slug": "viewer"},
    ],
    "groups": [
        {"name": "Staff", "slug": "staff", "roles": ["editor", "viewer"]},
    ],
    "role_grants": [
        {"role": "manager", "scope": "access",  "actions": ["read", "write"], "context": {}},
        {"role": "editor",  "scope": "articles", "actions": ["write"],        "context": {}},
        {"role": "viewer",  "scope": "articles", "actions": ["read"],         "context": {}},
    ],
}
```

Load the preset:

```bash
python manage.py load_permission_preset
python manage.py load_permission_preset --force
```

### Auto-Discovery from Apps

Each app exports from `permissions.py`:

```python
# orders/permissions.py
from django.utils.translation import gettext_lazy as _

PERMISSION_PRESET = {
    "actions": {
        "orders": {
            "create":  {"implies": [],          "label": _("Create")},
            "approve": {"implies": ["create"],   "label": _("Approve")},
        },
    },
    "roles": [
        {"name": "Order Manager", "slug": "order-manager"},
    ],
    "role_grants": [
        {"role": "order-manager", "scope": "orders",
         "actions": ["create", "approve"], "context": {}},
    ],
}

# Scopes with translatable labels for the frontend
ACCESS_SCOPES = [
    {"key": "orders", "label": _("Orders")},
]

ACCESS_APPLICATION_NAME = "orders"
```

## Permission String Format

| Format | Meaning |
|---|---|
| `orders:create` | Single action |
| `orders:create/approve` | **AND** — must have `create` **and** `approve` |
| `orders:create\|approve` | **OR** — must have `create` **or** `approve` |
| `orders:create/approve:manager` | AND + role filter |
| `orders:create\|approve:manager` | OR + role filter |
| `orders:create/approve?tenant_id=42` | AND + context |

## API Endpoints

```
GET    /api/access/scopes                         → list all scopes
GET    /api/access/scopes/{scope}/actions          → actions with translated labels

GET    /api/access/roles                           → list roles
GET    /api/access/groups                          → list groups
POST   /api/access/groups                          → create group
PUT    /api/access/groups/{slug}                   → update group
DELETE /api/access/groups/{slug}                   → delete group

POST   /api/access/users/assign-role               → assign role to user
POST   /api/access/users/revoke-role               → revoke role
POST   /api/access/users/assign-group              → assign group
POST   /api/access/users/revoke-group              → revoke group
POST   /api/access/users/override-grant            → override grant

GET    /api/access/users/{id}/grants               → user grants
GET    /api/access/users/{id}/groups               → user groups

GET    /api/access/role-grants                     → list role grants
POST   /api/access/role-grants                     → create role grant
PUT    /api/access/role-grants/{id}                → update role grant
DELETE /api/access/role-grants/{id}                → delete role grant
PUT    /api/access/grants/{id}                     → update grant
```

### Scope Actions Endpoint (NEW in 0.5.0)

```http
GET /api/access/scopes/orders/actions
```

```json
{
    "scope": "orders",
    "actions": [
        {"key": "create",  "label": "Créer"},
        {"key": "approve", "label": "Approuver"},
        {"key": "cancel",  "label": "Annuler"},
        {"key": "read",    "label": "Lire"}
    ]
}
```

### Scopes Endpoint (NEW in 0.5.0)

```http
GET /api/access/scopes
```

```json
[
    {"key": "orders",   "label": "Commandes"},
    {"key": "articles", "label": "Articles"},
    {"key": "users",    "label": "Utilisateurs"}
]
```

> 💡 The `label` is resolved in the active locale — use `_()` in your `ACCESS_SCOPES`
> definitions to get translated scope names for free.

## Usage

### Basic Permission Check

```python
from oxutils.permissions.utils import check, str_check

# AND: all actions required
check(user, 'orders', ['create', 'approve'])       # True if has both

# String check — single action
str_check(user, 'orders:create')

# AND (must have both)
str_check(user, 'orders:create/approve')

# OR (at least one)
str_check(user, 'orders:create|approve')

# With role filter
str_check(user, 'orders:create/approve:manager')

# With context
str_check(user, 'orders:create?tenant_id=42')
```

### OR Checks

```python
from oxutils.permissions.utils import any_action_check, any_permission_check

# OR on a single scope
any_action_check(user, 'orders', ['create', 'approve', 'cancel'])

# OR across different scopes/permissions
any_permission_check(
    user,
    'orders:create|approve',
    'articles:read',
    'users:read/write:admin',
)
```

### Controller-Level Permissions

```python
from oxutils.permissions.perms import (
    ScopePermission, ScopeAnyActionPermission, ScopeAnyPermission
)

# AND — must have create AND approve
@api_controller('/orders', permissions=[ScopePermission('orders:create/approve')])
class OrderController:
    pass

# OR — must have create OR approve
@api_controller('/orders', permissions=[ScopePermission('orders:create|approve')])
class FlexibleController:
    pass

# Always OR (ignores separator)
@api_controller('/orders', permissions=[
    ScopeAnyActionPermission('orders:create/approve/cancel')
])
class AnyController:
    pass

# OR across multiple permissions
@api_controller('/dashboard', permissions=[
    ScopeAnyPermission('orders:create|approve', 'articles:read')
])
class DashboardController:
    pass

# Access manager (for built-in /access endpoints)
from oxutils.permissions.perms import access_manager

@api_controller('/admin', permissions=[IsAuthenticated & access_manager('read/write')])
class AdminController:
    pass
```

### Frontend — Action Labels

```python
from oxutils.permissions.actions import get_action_label, get_scope_actions_labels

# Single label
get_action_label('orders', 'create')  # → "Créer" (in French locale)

# All labels for a scope
get_scope_actions_labels('orders')
# → {"create": "Créer", "approve": "Approuver", "cancel": "Annuler", ...}
```

### Assign / Revoke / Override

```python
from oxutils.permissions.utils import assign_role, revoke_role, override_grant

assign_role(user, 'editor', 'articles', by=admin)
revoke_role(user, 'editor', 'articles')
override_grant(user, 'articles', ['publish'])   # sets locked=True
override_grant(user, 'articles', [])             # deletes grant
```

### Activate / Deactivate

```python
from oxutils.permissions.utils import activate_user_permissions, deactivate_user_permissions

deactivate_user_permissions(user)                     # all scopes
deactivate_user_permissions(user, scope='articles')   # single scope
activate_user_permissions(user)
```

### Sync After Changes

```python
from oxutils.permissions.utils import group_sync, role_sync

# After modifying a RoleGrant, sync affected users
group_sync('staff')
group_sync('staff', role_slugs=['editor'], scope='articles')
role_sync('editor', scope='articles')
```

## Permission Classes Comparison

| Class | Logic | Example |
|---|---|---|
| `ScopePermission` | Respects `/` (AND) or `\|` (OR) | `'orders:create/approve'` |
| `ScopeAnyActionPermission` | Always OR | `'orders:create/approve'` → OR |
| `ScopeAnyPermission` | OR across multiple strings | `'orders:create\|approve', 'articles:read'` |

## Migration from 0.4.x

1. **Actions**: Replace single-letter actions (`r`, `w`, `d`, `u`, `a`) with named actions
   in `PERMISSION_PRESET["actions"]`.
2. **RoleGrants**: `actions: ["r", "w"]` → `actions: ["read", "write"]`.
3. **Permission strings**: `'articles:rw'` → `'articles:read/write'` (AND) or `'articles:read|write'` (OR).
4. **Controllers**: `access_manager('rw')` → `access_manager('read/write')`.
5. **Run migration** `0010_increase_action_max_length` (included).
6. **Define actions** per scope in `PERMISSION_PRESET["actions"]` with `implies` and optional `label`.

## Best Practices

1. **Define actions per scope** — each scope in its owning app.
2. **Always add `label`** to every action and scope — the frontend needs them for i18n.
   Use `gettext_lazy` (`_()`) so they're resolved in the user's locale.
3. **Use `implies`** for natural hierarchies (approve → create, publish → write → read).
4. **Sync after changes** — always call `group_sync()` / `role_sync()` after modifying `RoleGrant`.
5. **Use context for multi-tenancy** — filter grants with `tenant_id`, `department`, etc.
6. **One scope = one app** — strict ownership prevents conflicts.
7. **Use dict format for `ACCESS_SCOPES`** when the scope is displayed in the frontend —
   `{"key": "orders", "label": _("Orders")}` gives you i18n for free.
