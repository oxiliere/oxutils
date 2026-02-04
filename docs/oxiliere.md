# Oxiliere Module

**Multi-tenant architecture with django-tenants integration**

## Features

- Multi-tenant database isolation using PostgreSQL schemas
- Header-based tenant routing (`X-Organization-ID`)
- Tenant and user management
- Permission system for tenant access control
- Tenant initialization API
- Caching layer for tenant queries
- Middleware for automatic tenant switching
- Service-to-service authentication

## Overview

The Oxiliere module provides a complete multi-tenant solution for Django applications. Each tenant (organization) gets its own PostgreSQL schema, ensuring complete data isolation. Tenants are identified by their `oxi_id` (organization ID) passed via HTTP headers.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Public Schema (shared)            │
│  - Tenant metadata                          │
│  - User accounts                            │
│  - TenantUser relationships                 │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ tenant_acme │ │ tenant_corp │ │ tenant_demo │
│  (Schema)   │ │  (Schema)   │ │  (Schema)   │
│             │ │             │ │             │
│ - Orders    │ │ - Orders    │ │ - Orders    │
│ - Products  │ │ - Products  │ │ - Products  │
│ - Invoices  │ │ - Invoices  │ │ - Invoices  │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install django-tenants psycopg2-binary django-cacheops
```

### 2. Configure Settings

```python
# settings.py
from oxutils.conf import UTILS_APPS

# Database configuration (PostgreSQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'mydb',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Tenant configuration
TENANT_MODEL = "oxiliere.Tenant"
TENANT_DOMAIN_MODEL = "oxiliere.Domain"

# Shared apps (available in all schemas)
SHARED_APPS = [
    'django_tenants',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'oxutils.oxiliere',  # Tenant management
    'oxutils.users',     # User management
]

# Tenant-specific apps (isolated per tenant)
TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'myapp',  # Your tenant-specific app
]

INSTALLED_APPS = [
    *SHARED_APPS,
    *TENANT_APPS,
]

# Middleware (IMPORTANT: Order matters!)
MIDDLEWARE = [
    'oxutils.jwt.middleware.JWTCookieAuthMiddleware', # Must be first!
    'oxutils.oxiliere.middleware.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Organization header key
from oxutils.constants import ORGANIZATION_HEADER_KEY
# ORGANIZATION_HEADER_KEY = 'X-Organization-ID'

# Service authentication token (for internal services)
OXILIERE_SERVICE_TOKEN = 'your-secret-service-token'

# Optional: System tenant for administrative tasks
OXI_SYSTEM_TENANT = 'oxisystem'
```

### 3. Run Migrations

```bash
# Migrate shared schema (public)
python manage.py migrate_schemas --shared

# Migrate all tenant schemas
python manage.py migrate_schemas
```

## Models

### Tenant

Represents an organization with its own isolated database schema.

**Fields:**
- `schema_name` (CharField): PostgreSQL schema name (auto-generated)
- `name` (CharField): Organization display name
- `oxi_id` (UUIDField): Unique organization identifier
- `subscription_plan` (CharField): Subscription plan name
- `subscription_status` (CharField): Subscription status
- `subscription_end_date` (DateTimeField): Subscription expiry
- `status` (CharField): Tenant status (ACTIVE, INACTIVE, SUSPENDED)
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

### Domain

Maps domains to tenants (from django-tenants).

**Fields:**
- `domain` (CharField): Domain name
- `tenant` (ForeignKey): Related tenant
- `is_primary` (BooleanField): Primary domain flag

### TenantUser

Links users to tenants with role information.

**Fields:**
- `tenant` (ForeignKey): Related tenant
- `user` (ForeignKey): Related user
- `is_owner` (BooleanField): Owner flag
- `is_admin` (BooleanField): Admin flag
- `status` (CharField): User status in tenant

**Constraints:**
- Unique constraint on (tenant, user) pair

## Usage

### Creating a Tenant

#### Via API (Recommended)

```python
# POST /api/setup/init
# Headers: X-Oxiliere-Service-Token: your-secret-token

{
  "tenant": {
    "name": "Acme Corporation",
    "oxi_id": "acme-corp",
    "subscription_plan": "premium",
    "subscription_status": "active",
    "subscription_end_date": "2026-12-31T23:59:59Z",
    "status": "active"
  },
  "owner": {
    "oxi_id": "user-uuid",
    "email": "owner@acme.com"
  }
}
```

#### Programmatically

```python
from oxutils.oxiliere.schemas import CreateTenantSchema

schema = CreateTenantSchema(
    tenant={
        'name': 'Acme Corporation',
        'oxi_id': 'acme-corp',
        'subscription_plan': 'premium',
        'subscription_status': 'active',
    },
    owner={
        'oxi_id': 'user-uuid',
        'email': 'owner@acme.com'
    }
)

tenant = schema.create_tenant()
```

#### Using Management Command

```python
# management/commands/create_tenant.py
from django.core.management.base import BaseCommand
from oxutils.oxiliere.schemas import CreateTenantSchema

class Command(BaseCommand):
    help = 'Create a new tenant'
    
    def add_arguments(self, parser):
        parser.add_argument('--name', required=True)
        parser.add_argument('--oxi-id', required=True)
        parser.add_argument('--owner-email', required=True)
        parser.add_argument('--owner-id', required=True)
    
    def handle(self, *args, **options):
        schema = CreateTenantSchema(
            tenant={
                'name': options['name'],
                'oxi_id': options['oxi_id'],
            },
            owner={
                'oxi_id': options['owner_id'],
                'email': options['owner_email']
            }
        )
        
        tenant = schema.create_tenant()
        self.stdout.write(f"Created tenant: {tenant.name}")
```

### Making Requests with Tenant Context

All requests must include the `X-Organization-ID` header:

```bash
curl -H "X-Organization-ID: acme-corp" \
     -H "Authorization: Bearer <token>" \
     https://api.example.com/api/orders
```

```python
# Python requests
import requests

headers = {
    'X-Organization-ID': 'acme-corp',
    'Authorization': 'Bearer <token>'
}

response = requests.get('https://api.example.com/api/orders', headers=headers)
```

```javascript
// JavaScript fetch
fetch('https://api.example.com/api/orders', {
  headers: {
    'X-Organization-ID': 'acme-corp',
    'Authorization': 'Bearer <token>'
  }
})
```

### Accessing Tenant in Views

```python
from django.http import JsonResponse

def my_view(request):
    # Tenant is automatically set by middleware
    tenant = request.tenant
    
    return JsonResponse({
        'tenant_name': tenant.name,
        'tenant_id': str(tenant.oxi_id),
        'schema': tenant.schema_name
    })
```

### Querying Tenant Data

```python
from myapp.models import Order

def list_orders(request):
    # Queries are automatically scoped to current tenant's schema
    orders = Order.objects.all()
    
    # This only returns orders for the current tenant
    return JsonResponse({
        'orders': list(orders.values())
    })
```

## Middleware

### TenantMainMiddleware

Automatically switches database schema based on `X-Organization-ID` header.

**Flow:**
1. Extract `X-Organization-ID` from request headers
2. Look up tenant in public schema
3. Switch database connection to tenant's schema
4. Set `request.tenant` for view access
5. Handle missing tenant scenarios

**Error Handling:**
- Missing header: Returns 400 Bad Request
- Tenant not found: Returns 404 or shows public schema (configurable)

**Configuration:**

```python
# settings.py

# Show public schema if tenant not found (default: raise 404)
SHOW_PUBLIC_IF_NO_TENANT_FOUND = False

# Custom view for tenant not found
DEFAULT_NOT_FOUND_TENANT_VIEW = 'myapp.views.tenant_not_found'
```

## Permissions

The permission system uses `TokenTenant` from the middleware to verify user access rights. All tenant permissions check that `request.tenant` is a valid `TokenTenant` instance with the appropriate user relationship.

### Available Permission Classes

| Permission | Description | Use Case |
|------------|-------------|----------|
| `TenantUserPermission` / `IsTenantUser` | User is a member of the current tenant | General tenant access |
| `TenantOwnerPermission` / `IsTenantOwner` | User is the owner of the tenant | Sensitive operations |
| `TenantAdminPermission` / `IsTenantAdmin` | User is admin or owner of the tenant | Administrative functions |
| `OxiliereServicePermission` / `IsOxiliereService` | Request from internal Oxiliere service | Internal APIs |

### TenantUserPermission (IsTenantUser)

Verifies the user is an active member of the current tenant.

```python
from ninja_extra import api_controller, http_get
from oxutils.oxiliere.permissions import TenantUserPermission, IsTenantUser

# Using class
@api_controller('/orders', permissions=[TenantUserPermission()])
class OrderController:
    @http_get('/')
    def list_orders(self, request):
        # User must be a member of the tenant
        return Order.objects.all()

# Using singleton instance (recommended)
@api_controller('/products', permissions=[IsTenantUser])
class ProductController:
    @http_get('/')
    def list_products(self, request):
        pass
```

**Requirements:**
- `request.user` must be authenticated
- `request.tenant` must be a `TokenTenant` instance
- `request.tenant.user` must exist and be active (`is_tenant_user` property)

### TenantOwnerPermission (IsTenantOwner)

Verifies the user is the owner of the current tenant.

```python
from oxutils.oxiliere.permissions import TenantOwnerPermission, IsTenantOwner

@api_controller('/settings', permissions=[IsTenantOwner])
class SettingsController:
    @http_post('/update')
    def update_settings(self, request, payload):
        # Only tenant owner can access
        pass
```

**Requirements:**
- All `TenantUserPermission` requirements
- `request.tenant.user.is_owner` must be `True`

### TenantAdminPermission (IsTenantAdmin)

Verifies the user is an admin or owner of the current tenant.

```python
from oxutils.oxiliere.permissions import TenantAdminPermission, IsTenantAdmin

@api_controller('/users', permissions=[IsTenantAdmin])
class UserManagementController:
    @http_post('/invite')
    def invite_user(self, request, email: str):
        # Only admins and owners can access
        pass
```

**Requirements:**
- All `TenantUserPermission` requirements
- `request.tenant.user.is_admin` must be `True`

### OxiliereServicePermission (IsOxiliereService)

Verifies request comes from an internal Oxiliere service.

```python
from oxutils.oxiliere.permissions import OxiliereServicePermission, IsOxiliereService

@api_controller('/setup', permissions=[IsOxiliereService])
class SetupController:
    @http_post('/init')
    def init_tenant(self, payload):
        # Only internal services can access
        # Requires X-Oxiliere-Service-Token header
        pass
```

**Header Required:**
```http
X-Oxiliere-Service-Token: <service-token>
```

### Custom Tenant Permissions

Extend `TenantBasePermission` to create custom tenant-based permissions:

```python
from oxutils.oxiliere.permissions import TenantBasePermission

class TenantBillingPermission(TenantBasePermission):
    """Custom permission for billing operations."""
    
    def check_tenant_permission(self, request) -> bool:
        tenant = request.tenant
        # Custom logic here
        return tenant.subscription_plan in ['premium', 'enterprise']

# Usage
@api_controller('/billing', permissions=[TenantBillingPermission()])
class BillingController:
    pass
```

### How Permissions Work

1. **Base Check** (`TenantBasePermission.has_permission`):
   - Verifies `request.user.is_authenticated`
   - Verifies `request.tenant` exists and is a `TokenTenant`
   - Calls `check_tenant_permission()` for specific logic

2. **TokenTenant Properties**:
   - `is_tenant_user`: True if user exists and is active
   - `is_owner_user`: True if user is owner
   - `is_admin_user`: True if user is admin

3. **Logging**: All permission checks are logged with structured logging:
   ```python
   logger.info('tenant_permission', 
               type="tenant_user_access_permission",
               tenant=tenant, 
               user=request.user,
               passed=True)
   ```

### Combining Permissions

```python
from ninja_extra.permissions import AND, OR, NOT
from oxutils.oxiliere.permissions import IsTenantAdmin, IsTenantOwner

# Admin OR Owner
@api_controller('/admin', permissions=[OR(IsTenantAdmin, IsTenantOwner)])
class AdminController:
    pass

# Owner AND specific condition
@api_controller('/delete', permissions=[AND(IsTenantOwner, CustomPermission())])
class DeleteController:
    pass
```

## Utilities

### oxid_to_schema_name()

Converts organization ID to valid PostgreSQL schema name.

```python
from oxutils.oxiliere.utils import oxid_to_schema_name

schema_name = oxid_to_schema_name('acme-corp')
# Returns: 'tenant_acmecorp'

schema_name = oxid_to_schema_name('my-company-123')
# Returns: 'tenant_mycompany123'
```

**Rules:**
- Replaces hyphens with underscores
- Removes non-alphanumeric characters
- Prefixes with `tenant_`
- Converts to lowercase
- Maximum 63 characters (PostgreSQL limit)

### update_tenant()

Updates tenant information from external data.

```python
from oxutils.oxiliere.utils import update_tenant

update_tenant('acme-corp', {
    'name': 'Acme Corporation Inc.',
    'subscription_status': 'active',
    'subscription_end_date': '2026-12-31'
})
```

### update_tenant_user()

Updates tenant user relationship.

```python
from oxutils.oxiliere.utils import update_tenant_user

update_tenant_user('acme-corp', 'user-uuid', {
    'is_admin': True,
    'status': 'active'
})
```

## Caching

The module includes caching for frequently accessed tenant data:

```python
from oxutils.oxiliere.caches import (
    get_tenant_by_oxi_id,
    get_tenant_by_schema_name,
    get_tenant_user,
    get_system_tenant
)

# Cached for 15 minutes
tenant = get_tenant_by_oxi_id('acme-corp')

# Cached tenant user relationship
tenant_user = get_tenant_user('acme-corp', 'user-uuid')
```

**Cache Configuration:**

```python
# settings.py
CACHEOPS = {
    'oxiliere.tenant': {'ops': 'all', 'timeout': 60*15},
    'oxiliere.tenantuser': {'ops': 'all', 'timeout': 60*15},
}
```

## Management Commands

### migrate_schemas

Migrate all tenant schemas:

```bash
# Migrate shared schema only
python manage.py migrate_schemas --shared

# Migrate all tenant schemas
python manage.py migrate_schemas

# Migrate specific tenant
python manage.py migrate_schemas --schema=tenant_acmecorp
```

### create_tenant_superuser

Create superuser for a specific tenant:

```bash
python manage.py create_tenant_superuser --schema=tenant_acmecorp
```

## API Reference

### SetupController

**Endpoint:** `/api/setup/init`

**Method:** POST

**Authentication:** Service token required

**Headers:**
- `X-Oxiliere-Service-Token`: Service authentication token

**Request Body:**
```json
{
  "tenant": {
    "name": "Organization Name",
    "oxi_id": "org-slug",
    "subscription_plan": "premium",
    "subscription_status": "active",
    "subscription_end_date": "2026-12-31T23:59:59Z",
    "status": "active"
  },
  "owner": {
    "oxi_id": "user-uuid",
    "email": "owner@example.com"
  }
}
```

**Response:**
```json
{
  "code": "success",
  "detail": "Tenant initialized successfully"
}
```

## Best Practices

1. **Always Use Headers**: Include `X-Organization-ID` in all tenant-scoped requests
2. **Cache Tenant Lookups**: Use provided cache functions for performance
3. **Validate Permissions**: Use permission classes for tenant access control
4. **Handle Missing Tenants**: Configure appropriate error handling
5. **Monitor Schema Count**: Keep track of tenant count for database performance
6. **Regular Backups**: Backup all schemas, not just public
7. **Test Isolation**: Ensure data isolation between tenants in tests
8. **Use Transactions**: Wrap tenant creation in atomic transactions
9. **Log Tenant Context**: Include tenant ID in all logs
10. **Service Authentication**: Protect internal endpoints with service tokens

## Security Considerations

1. **Schema Isolation**: Each tenant has complete database isolation
2. **Header Validation**: Middleware validates tenant existence
3. **Permission Checks**: Use permission classes for access control
4. **Service Tokens**: Protect internal APIs with service authentication
5. **User-Tenant Binding**: Verify user belongs to tenant before access
6. **SQL Injection**: PostgreSQL schemas prevent cross-tenant queries
7. **Audit Logging**: Log all tenant access and modifications

## Testing

### Test with Specific Tenant

```python
from django.test import TestCase
from django_tenants.test.cases import TenantTestCase
from oxutils.oxiliere.models import Tenant

class MyTestCase(TenantTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = Tenant.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            oxi_id='test-tenant'
        )
    
    def test_something(self):
        # Tests run in tenant schema
        pass
```

### Test with Header

```python
from django.test import Client

def test_api_with_tenant():
    client = Client()
    response = client.get(
        '/api/orders/',
        HTTP_OXI_ORG_ID='acme-corp'
    )
    assert response.status_code == 200
```

## Troubleshooting

### Missing X-Organization-ID Header

**Error:** 400 Bad Request

**Solution:** Include header in all requests:
```python
headers = {'X-Organization-ID': 'your-tenant-id'}
```

### Tenant Not Found

**Error:** 404 Not Found

**Solution:** Verify tenant exists and `oxi_id` is correct:
```python
from oxutils.oxiliere.models import Tenant
Tenant.objects.filter(oxi_id='your-id').exists()
```

### Schema Name Too Long

**Error:** ValueError: Schema name too long

**Solution:** Use shorter organization IDs (max ~55 characters after `tenant_` prefix)

### Permission Denied

**Error:** 403 Forbidden

**Solution:** Verify user is linked to tenant:
```python
from oxutils.oxiliere.models import TenantUser
TenantUser.objects.filter(tenant__oxi_id='tenant-id', user=user).exists()
```

## Migration from Single-Tenant

1. Create public schema with tenant metadata
2. Migrate existing data to tenant schema
3. Update application to use tenant middleware
4. Add `X-Organization-ID` header to all requests
5. Test data isolation thoroughly

## Dependencies

- `django-tenants`: Multi-tenant PostgreSQL schemas
- `psycopg2-binary`: PostgreSQL adapter
- `django-cacheops`: Query caching
- `structlog`: Structured logging
- `ninja-extra`: REST API framework
