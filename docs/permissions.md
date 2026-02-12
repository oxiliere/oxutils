# Permissions System

**Flexible role-based access control with groups and custom grants**

## Features

- Role-based permissions with hierarchical actions
- Group management for bulk role assignment
- Custom grant overrides per user
- RoleGrant templates for role permissions
- Automatic synchronization after changes
- Bulk operations for performance
- Full traceability with `created_by` tracking
- Context-based permission filtering

## Setup

Add to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'oxutils.permissions',
]
```

Run migrations:

```bash
python manage.py migrate permissions
```

## Core Concepts

### Architecture

```
User ──> UserGroup ──> Group ──> Role ──> RoleGrant
  │                                          │
  └──────────> Grant <────────────────────────┘
```

### Models

**Role**: Named set of permissions (e.g., `admin`, `editor`)

**Group**: Collection of roles for easier assignment (e.g., `staff`)

**RoleGrant**: Permission template for a role on a scope
- Applies to all users with the role

**Grant**: Effective user permission on a scope
- **Inherited**: `role != None` (from RoleGrant)
- **Custom**: `role = None` (after override)

**UserGroup**: Links user to group for traceability

### Actions Hierarchy

Actions have dependencies that are automatically expanded:

- `r`: Read
- `w`: Write (implies `r`)
- `d`: Delete (implies `w`, `r`)

Example: Granting `['w']` automatically gives `['r', 'w']`

## Configuration

### Required Settings

```python
# settings.py

# Access manager configuration
ACCESS_MANAGER_SCOPE = "access"      # Scope for access management endpoints
ACCESS_MANAGER_GROUP = "manager"     # Group for UserGroup assignment in authorization (or None)
ACCESS_MANAGER_ROLE = "admin"        # Role for permission check filtering (or None)
ACCESS_MANAGER_CONTEXT = {}          # Additional context dict

# List of valid scopes in your application
ACCESS_SCOPES = [
    "access",
    "users",
    "articles",
    "comments"
]

# Enable permission check caching (requires cacheops)
CACHE_CHECK_PERMISSION = False

# if cacheops is installed, enable caching
if 'cacheops' in settings.INSTALLED_APPS:
    CACHE_CHECK_PERMISSION = True

# and add "oxutils.permissions.*" in cacheops settings
```

### Permission Preset

Define initial permissions in settings:

```python
# settings.py
PERMISSION_PRESET = {
    "roles": [
        {"name": "Admin", "slug": "admin"},
        {"name": "Editor", "slug": "editor"},
        {"name": "Viewer", "slug": "viewer"}
    ],
    "group": [
        {
            "name": "Staff",
            "slug": "staff",
            "roles": ["editor", "viewer"]
        },
        {
            "name": "Premium Staff",
            "slug": "premium-staff",
            "roles": ["editor"]
        }
    ],
    "role_grants": [
        {
            "role": "admin",
            "scope": "users",
            "actions": ["r", "w", "d"],
            "context": {}
        },
        {
            "role": "editor",
            "scope": "articles",
            "actions": ["r", "w"],
            "context": {}
        }
    ]
}
```

Load the preset:

```bash
python manage.py load_permission_preset

# Force reload (careful with duplicates)
python manage.py load_permission_preset --force
```

## API Endpoints

All endpoints are prefixed with `/api/access/` (configurable in router).

### Roles

```http
GET    /api/access/roles              # List all roles
POST   /api/access/roles              # Create role
GET    /api/access/roles/{slug}       # Get role details
PUT    /api/access/roles/{slug}       # Update role
DELETE /api/access/roles/{slug}       # Delete role
```

### Groups

```http
GET    /api/access/groups             # List all groups
POST   /api/access/groups             # Create group
GET    /api/access/groups/{slug}      # Get group details
PUT    /api/access/groups/{slug}      # Update group
DELETE /api/access/groups/{slug}      # Delete group
POST   /api/access/groups/{slug}/sync # Sync group users
```

### User Assignment

```http
POST /api/access/users/assign-role    # Assign role to user
POST /api/access/users/revoke-role    # Revoke role from user
POST /api/access/users/assign-group   # Assign group to user
POST /api/access/users/revoke-group   # Revoke group from user
```

### Grants

```http
GET    /api/access/grants             # List grants
POST   /api/access/grants             # Create custom grant
PUT    /api/access/grants/{id}        # Update grant
DELETE /api/access/grants/{id}        # Delete grant
```

### RoleGrants

```http
GET    /api/access/role-grants        # List role grants
POST   /api/access/role-grants        # Create role grant
PUT    /api/access/role-grants/{id}   # Update role grant
DELETE /api/access/role-grants/{id}   # Delete role grant
```

## Usage

### Basic Permission Check

```python
from oxutils.permissions.utils import check, str_check

# Simple check (ALL actions required)
if check(user, 'articles', ['r']):
    # User can read articles
    pass

# Check with context
if check(user, 'articles', ['w'], tenant_id=123):
    # User can write articles for tenant 123
    pass

# Check with role filter
if check(user, 'articles', ['w'], role='editor'):
    # User can write articles via editor role
    pass

# String-based check (convenient format)
if str_check(user, 'articles:r'):
    # User can read articles
    pass

# String check with role
if str_check(user, 'articles:w:editor'):
    # User can write articles via editor role
    pass

# String check with context (query params)
if str_check(user, 'articles:w?tenant_id=123&status=published'):
    # User can write published articles for tenant 123
    pass

# String check with role and context
if str_check(user, 'articles:w:editor?tenant_id=123'):
    # User can write articles for tenant 123 via editor role
    pass
```

### "Any" Permission Checks (OR Logic)

For checking if a user has **at least one** of multiple permissions:

```python
from oxutils.permissions.utils import any_action_check, any_permission_check

# Check if user has AT LEAST ONE action on a scope
if any_action_check(user, 'articles', ['r', 'w', 'd']):
    # User has read OR write OR delete permission
    pass

# With role filter
if any_action_check(user, 'articles', ['w', 'd'], role='editor'):
    # User has write OR delete via editor role
    pass

# With context
if any_action_check(user, 'articles', ['r', 'w'], tenant_id=123):
    # User has read OR write for tenant 123
    pass

# Check if user has AT LEAST ONE of multiple permissions
if any_permission_check(
    user,
    'articles:r',              # Can read articles
    'articles:w:editor',       # OR can write as editor
    'invoices:d:admin'         # OR can delete invoices as admin
):
    # User has at least one of these permissions
    pass

# Complex example with different scopes and contexts
if any_permission_check(
    user,
    'reports:r?department=finance',
    'reports:w:admin',
    'analytics:r'
):
    # User can access if they have ANY of these permissions
    pass
```

**Performance Note:** Both functions use a single optimized database query with OR conditions, regardless of how many permissions are checked.

### Controller-Level Permissions

#### ScopePermission (AND Logic)

Use `ScopePermission` to protect entire controllers or specific routes. User must have **ALL** specified actions:

```python
from ninja_extra import api_controller, http_get
from oxutils.permissions.perms import ScopePermission

# Protect entire controller
@api_controller('/articles', permissions=[ScopePermission('articles:w')])
class ArticleController:
    @http_get('/')
    def list_articles(self):
        # Only users with write permission on articles can access
        pass

# With role-specific permission
@api_controller('/admin', permissions=[ScopePermission('users:w:admin')])
class AdminController:
    pass

# With context in permission string
@api_controller('/reports', permissions=[ScopePermission('reports:r?department=finance')])
class ReportController:
    pass

# Method-level permission (override controller permission)
@api_controller('/articles')
class ArticleController:
    @http_get('/', permissions=[ScopePermission('articles:r')])
    def list_articles(self):
        # Read-only access
        pass
    
    @http_post('/', permissions=[ScopePermission('articles:w')])
    def create_article(self):
        # Write access required
        pass
```

#### ScopeAnyActionPermission (OR Logic - Single Scope)

Use when user needs **at least one** of multiple actions on a single scope:

```python
from oxutils.permissions.perms import ScopeAnyActionPermission

# User needs read OR write OR delete on articles
@api_controller('/articles', permissions=[
    ScopeAnyActionPermission('articles:rwd')
])
class ArticleController:
    # Access granted if user has ANY of: read, write, or delete
    pass

# With role filter
@api_controller('/reports', permissions=[
    ScopeAnyActionPermission('reports:rw:admin')
])
class ReportController:
    # User needs read OR write via admin role
    pass

# With context
@api_controller('/invoices', permissions=[
    ScopeAnyActionPermission('invoices:rwd?tenant_id=123')
])
class InvoiceController:
    # User needs read OR write OR delete for tenant 123
    pass

# With additional context via ctx parameter
@api_controller('/data', permissions=[
    ScopeAnyActionPermission('data:rw', ctx={'department': 'finance'})
])
class DataController:
    pass
```

#### ScopeAnyPermission (OR Logic - Multiple Permissions)

Use when user needs **at least one** of multiple complete permissions (can be different scopes):

```python
from oxutils.permissions.perms import ScopeAnyPermission

# User needs ANY of these permissions
@api_controller('/dashboard', permissions=[
    ScopeAnyPermission(
        'articles:r',           # Can read articles
        'invoices:w:accountant',# OR can write invoices as accountant
        'reports:r:admin'       # OR can read reports as admin
    )
])
class DashboardController:
    # Access granted if user has at least one permission
    pass

# Complex example with different scopes and contexts
@api_controller('/analytics', permissions=[
    ScopeAnyPermission(
        'analytics:r',
        'reports:r?department=finance',
        'data:w:admin'
    )
])
class AnalyticsController:
    # User needs ANY of these permissions to access
    pass

# Combining with method-level permissions
@api_controller('/content')
class ContentController:
    @http_get('/', permissions=[
        ScopeAnyPermission('articles:r', 'pages:r', 'posts:r')
    ])
    def list_content(self):
        # Can read articles OR pages OR posts
        pass
    
    @http_post('/', permissions=[
        ScopeAnyPermission('articles:w:editor', 'posts:w:editor')
    ])
    def create_content(self):
        # Can write articles as editor OR posts as editor
        pass
```

**Comparison:**

| Permission Class | Logic | Use Case |
|-----------------|-------|----------|
| `ScopePermission` | AND | User must have ALL actions (e.g., `'articles:rw'` = read AND write) |
| `ScopeAnyActionPermission` | OR | User needs ANY action on one scope (e.g., `'articles:rwd'` = read OR write OR delete) |
| `ScopeAnyPermission` | OR | User needs ANY complete permission (e.g., multiple scopes/roles) |

### Assign Role to User

```python
from oxutils.permissions.utils import assign_role

# Assign role directly
assign_role(user, 'editor', by=admin_user)

# This creates Grants based on RoleGrants for 'editor'
```

### Assign Group to User

```python
from oxutils.permissions.utils import assign_group

# Assign all roles from a group
user_group = assign_group(user, 'staff', by=admin_user)

# This:
# 1. Creates a UserGroup linking user to group
# 2. Assigns all roles from the group
```

### Revoke Permissions

```python
from oxutils.permissions.utils import revoke_role, revoke_group

# Revoke a single role
deleted_count, info = revoke_role(user, 'editor')

# Revoke entire group (removes all associated grants)
deleted_count, info = revoke_group(user, 'staff')
```

### Override User Permissions

```python
from oxutils.permissions.utils import override_grant

# User has ['r', 'w', 'd'] on articles via role
# Reduce to read-only
override_grant(user, 'articles', remove_actions=['w', 'd'])

# Grant becomes custom (role=None)
# Will NOT be affected by future group syncs
```

### Synchronize Group

After modifying RoleGrants or group roles, sync all users:

```python
from oxutils.permissions.utils import group_sync

# Sync all users in the group
stats = group_sync('staff')
# Returns: {"users_synced": 5, "grants_updated": 15}

# This:
# 1. Deletes old grants (except custom overrides)
# 2. Recreates grants from current RoleGrants
# 3. Preserves custom grants (role=None)
```

## Advanced Usage

### Role Permissions

```python
# RoleGrant for all editors
RoleGrant.objects.create(
    role=editor_role,
    scope='articles',
    actions=['r', 'w', 'd']
)

# All users with editor role get ['r', 'w', 'd']
assign_role(user1, 'editor')
assign_group(user2, 'staff')  # If staff group includes editor role
```

### Context-Based Permissions

```python
# Create grant with context
Grant.objects.create(
    user=user,
    scope='articles',
    actions=['r', 'w'],
    context={'tenant_id': 123, 'status': 'published'}
)

# Check with matching context
check(user, 'articles', ['w'], tenant_id=123, status='published')  # True
check(user, 'articles', ['w'], tenant_id=456)  # False
```

### Custom Grant Creation

```python
from oxutils.permissions.services import PermissionService

service = PermissionService()

# Create a custom grant (not tied to any role)
grant = service.create_grant({
    'user_id': user.id,
    'scope': 'reports',
    'actions': ['r', 'x'],
    'context': {'department': 'finance'}
})
```

## Service Layer

Use the service for business logic:

```python
from oxutils.permissions.services import PermissionService

service = PermissionService()

# Assign role with traceability
role = service.assign_role_to_user(
    user_id=user.id,
    role_slug='editor',
    by_user=admin_user
)

# Assign group
roles = service.assign_group_to_user(
    user_id=user.id,
    group_slug='staff',
    by_user=admin_user
)

# Sync group
stats = service.sync_group('staff')
```

## Workflow Examples

### Initial Setup

```python
# 1. Create roles
admin = Role.objects.create(slug='admin', name='Administrator')
editor = Role.objects.create(slug='editor', name='Editor')

# 2. Create RoleGrants
RoleGrant.objects.create(
    role=admin,
    scope='users',
    actions=['r', 'w', 'd']
)

RoleGrant.objects.create(
    role=editor,
    scope='articles',
    actions=['r', 'w']
)

# 3. Create group
staff = Group.objects.create(slug='staff', name='Staff')
staff.roles.add(editor)

# 4. Assign to users
assign_group(user, 'staff', by=admin_user)
```

### Modify Permissions Globally

```python
# Update RoleGrant
rg = RoleGrant.objects.get(role__slug='editor', scope='articles')
rg.actions = ['r', 'w', 'd']  # Add delete permission
rg.save()

# Sync all users in groups that have this role
group_sync('staff')

# All staff members now have delete permission
# EXCEPT those with custom overrides
```

### Handle Permission Abuse

```python
# User abuses permissions, reduce them
override_grant(user, 'articles', remove_actions=['d'])

# Grant becomes custom (role=None)
# Future group syncs won't affect this user's permissions on 'articles'
```

### Temporary Elevated Access

```python
# Give temporary admin access
assign_role(user, 'admin', by=manager)

# Later, revoke it
revoke_role(user, 'admin')

# User returns to their group permissions
```

## Performance

### Bulk Operations

The system uses bulk operations for optimal performance:

```python
# group_sync uses bulk_create with update_conflicts
# 100 users × 10 grants = 100 SQL queries (not 1000)
stats = group_sync('large-group')
```

### Permission Check Caching

Enable caching to improve permission check performance:

```python
# settings.py
CACHE_CHECK_PERMISSION = True

# Requires cacheops in INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'cacheops',
    'oxutils.permissions',
]

# Configure cacheops
CACHEOPS_REDIS = "redis://localhost:6379/1"
CACHEOPS = {
    'permissions.*': {'ops': 'all', 'timeout': 60*60},
}
```

**How it works:**

- When `CACHE_CHECK_PERMISSION = True`, permission checks are cached for 15 minutes
- Cache is automatically invalidated when `Grant` model changes
- Uses `cacheops` `@cached_as` decorator
- Falls back to non-cached checks if `CACHE_CHECK_PERMISSION = False`

**Cached functions:**

```python
from oxutils.permissions.caches import (
    cache_check,                    # Caches check()
    cache_any_action_check,         # Caches any_action_check()
    cache_any_permission_check      # Caches any_permission_check()
)

# All permission classes automatically use cached versions
ScopePermission('articles:r')              # Uses cache_check
ScopeAnyActionPermission('articles:rwd')   # Uses cache_any_action_check
ScopeAnyPermission('articles:r', 'invoices:w')  # Uses cache_any_permission_check
```

**Performance impact:**

```python
# Without cache: Database query every time
check(user, 'articles', ['r'])  # ~5-10ms
any_action_check(user, 'articles', ['r', 'w', 'd'])  # ~5-10ms
any_permission_check(user, 'articles:r', 'invoices:w')  # ~5-10ms

# With cache: Redis lookup after first check
check(user, 'articles', ['r'])  # ~0.5-1ms (10x faster)
any_action_check(user, 'articles', ['r', 'w', 'd'])  # ~0.5-1ms (10x faster)
any_permission_check(user, 'articles:r', 'invoices:w')  # ~0.5-1ms (10x faster)
```

**Note:** All permission check functions (`check`, `str_check`, `any_action_check`, `any_permission_check`) benefit from caching when enabled.

### Query Optimization

```python
# Grants use select_related for efficient queries
grant = Grant.objects.select_related('user_group', 'role').get(id=1)

# Indexes on frequently queried fields
# - (user, scope)
# - (user_group)
# - GIN indexes on actions and context (PostgreSQL)
```

## Exception Handling

Custom exceptions for clear error messages:

```python
from oxutils.permissions.exceptions import (
    RoleNotFoundException,
    GroupNotFoundException,
    GrantNotFoundException,
    RoleAlreadyAssignedException,
    GroupAlreadyAssignedException,
)

try:
    assign_role(user, 'invalid-role')
except RoleNotFoundException as e:
    # Handle: "Le rôle 'invalid-role' n'existe pas"
    pass
```

All exceptions are automatically converted to appropriate HTTP responses by the service layer.

## Database Constraints

### Unique Constraints

- **Role**: `unique(slug)`
- **Group**: `unique(slug)`
- **UserGroup**: `unique(user, group)`
- **RoleGrant**: `unique(role, scope)`
- **Grant**: `unique(user, scope, role, user_group)`

### Indexes

- Grant: `(user, scope)`, `(user_group)`, GIN on `actions`, GIN on `context`
- UserGroup: `(user, group)`
- RoleGrant: `(role)`, `(role, scope)`

## Best Practices

### 1. Use Groups for Organization

```python
# ✅ Good
assign_group(user, 'staff')

# ❌ Avoid (unless specific need)
assign_role(user, 'role1')
assign_role(user, 'role2')
assign_role(user, 'role3')
```

### 2. Define Clear RoleGrants

```python
# ✅ Good: Clear RoleGrant
RoleGrant.objects.create(
    role=editor,
    scope='articles',
    actions=['r', 'w']
)
```

### 3. Always Sync After Changes

```python
# Modify RoleGrant
role_grant.actions = ['r', 'w', 'd']
role_grant.save()

# ✅ Sync immediately
group_sync('staff')
```

### 4. Use Context for Multi-Tenancy

```python
# Grant with tenant context
Grant.objects.create(
    user=user,
    scope='data',
    actions=['r', 'w'],
    context={'tenant_id': 123}
)

# Check with tenant
check(user, 'data', ['w'], tenant_id=123)  # True
check(user, 'data', ['w'], tenant_id=456)  # False
```

### 5. Track Changes

```python
# Always pass by parameter for audit trail
assign_role(user, 'editor', by=admin_user)
assign_group(user, 'staff', by=admin_user)
```

### 6. Enable Caching for Production

```python
# settings.py
CACHE_CHECK_PERMISSION = True  # Enable in production

# Ensure cacheops is configured
INSTALLED_APPS = ['cacheops', ...]
CACHEOPS_REDIS = "redis://localhost:6379/1"
```

## Troubleshooting

### Permissions Not Applied

```python
# After modifying RoleGrants, sync the group
group_sync('staff')
```

### Override Not Working

```python
# Check if grant has role=None
grant = Grant.objects.get(user=user, scope='articles')
print(grant.role)  # Should be None for custom grant
```

### Cache Not Working

```python
# Verify cacheops is installed
python -c "import cacheops"

# Check settings
from django.conf import settings
print(settings.CACHE_CHECK_PERMISSION)  # Should be True
print('cacheops' in settings.INSTALLED_APPS)  # Should be True

# Clear cache manually if needed
from cacheops import invalidate_model
from oxutils.permissions.models import Grant
invalidate_model(Grant)
```

### Bulk Create Conflicts

```python
# Ensure unique constraint fields match
# Grant: unique(user, scope, role, user_group)
```

## Migration Notes

After model changes:

```bash
python manage.py makemigrations permissions
python manage.py migrate permissions
```

Key migrations:
- Initial: Creates all models with constraints and indexes
- RoleGrant unique constraint: `(role, scope)`
- Add `created_by` to Grant: Enables audit trail
- Update Grant constraint: Includes `user_group` in uniqueness

## Testing

```python
from django.test import TestCase
from oxutils.permissions.utils import assign_role, check

class PermissionsTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(slug='editor', name='Editor')
        RoleGrant.objects.create(
            role=self.role,
            scope='articles',
            actions=['r', 'w']
        )
    
    def test_role_assignment(self):
        assign_role(self.user, 'editor')
        
        self.assertTrue(check(self.user, 'articles', ['r']))
        self.assertTrue(check(self.user, 'articles', ['w']))
        self.assertFalse(check(self.user, 'articles', ['d']))
    
    def test_override(self):
        assign_role(self.user, 'editor')
        override_grant(self.user, 'articles', remove_actions=['w'])
        
        self.assertTrue(check(self.user, 'articles', ['r']))
        self.assertFalse(check(self.user, 'articles', ['w']))
```

## Related Documentation

- [Audit System](audit.md) - Track permission changes
- [Mixins](mixins.md) - BaseService pattern
- [Settings](settings.md) - Configuration options
