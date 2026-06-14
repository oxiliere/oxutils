"""
Signals for the oxiliere (tenants) module.

All signals use ``send_robust()`` — a failing receiver never blocks the operation.
"""
from django.dispatch import Signal

# ── Tenant lifecycle ───────────────────────────────────────────────

tenant_created = Signal()
"""
Fired when a new tenant is created (first save).

Args:
    sender: The Tenant model class.
    tenant: The newly created Tenant instance.
"""

tenant_deleted = Signal()
"""
Fired when a tenant is soft-deleted via ``delete_tenant()``.

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance being deleted.
"""

tenant_restored = Signal()
"""
Fired when a deleted tenant is restored via ``restore()``.

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance being restored.
"""

tenant_force_dropped = Signal()
"""
Fired when a tenant is hard-deleted via ``delete(force_drop=True)``.

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance (just before deletion — the object
            may no longer exist after the signal fires).
"""

tenant_subscription_changed = Signal()
"""
Fired when a tenant's subscription metadata changes
(plan, status, or end_date).

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance.
    previous: Dict with the old values {'plan', 'status', 'end_date'}.
"""

# ── Tenant membership ──────────────────────────────────────────────

tenant_user_added = Signal()
"""
Fired when a user is added to a tenant.

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance.
    user: The User that was added.
"""

tenant_user_removed = Signal()
"""
Fired when a user is removed from a tenant.

Args:
    sender: The Tenant model class.
    tenant: The Tenant instance.
    user: The User that was removed.
"""

tenant_user_role_changed = Signal()
"""
Fired when a TenantUser's role (is_owner / is_admin) or status changes.

Args:
    sender: The TenantUser model class.
    tenant_user: The TenantUser instance.
    previous: Dict with old values {'is_owner', 'is_admin', 'status'}.
"""

tenant_user_activated = Signal()
"""
Fired when a TenantUser's status changes to ACTIVE from a non-ACTIVE state.

Args:
    sender: The TenantUser model class.
    tenant_user: The TenantUser instance.
"""

tenant_user_deactivated = Signal()
"""
Fired when a TenantUser's status changes from ACTIVE to a non-ACTIVE state.

Args:
    sender: The TenantUser model class.
    tenant_user: The TenantUser instance.
"""
