"""
Tests for the permissions module (refactored — named actions).
"""
import pytest
from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from unittest.mock import Mock, patch, MagicMock

from oxutils.permissions.models import Role, Group, RoleGrant, Grant, UserGroup
from oxutils.permissions.utils import (
    activate_user_permissions,
    deactivate_user_permissions,
    assign_role,
    revoke_role,
    assign_group,
    revoke_group,
    override_grant,
    check,
    str_check,
    group_sync,
    role_sync,
    any_action_check,
    any_permission_check,
    parse_permission,
)
from oxutils.permissions.actions import (
    collapse_actions,
    expand_actions,
    get_valid_actions,
    get_implied_actions,
    get_action_label,
    get_scope_actions_labels,
)
from oxutils.permissions.exceptions import (
    RoleNotFoundException,
    GroupNotFoundException,
    GrantNotFoundException,
    GroupAlreadyAssignedException,
)
from oxutils.permissions.perms import (
    ScopePermission,
    ScopeAnyPermission,
    ScopeAnyActionPermission,
    access_manager,
    extra_permissions,
)
from oxutils.permissions import presets as presets_mod


User = get_user_model()


@pytest.fixture
def db_setup(db):
    """Setup database for tests."""
    pass


@pytest.fixture
def test_user(db_setup):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db_setup):
    """Create an admin user."""
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_staff=True
    )


@pytest.fixture
def editor_role(db_setup):
    """Create an editor role."""
    return Role.objects.create(slug='editor', name='Editor')


@pytest.fixture
def viewer_role(db_setup):
    """Create a viewer role."""
    return Role.objects.create(slug='viewer', name='Viewer')


@pytest.fixture
def admin_role(db_setup):
    """Create an admin role."""
    return Role.objects.create(slug='admin', name='Administrator')


@pytest.fixture
def staff_group(db_setup, editor_role, viewer_role):
    """Create a staff group with roles."""
    group = Group.objects.create(slug='staff', name='Staff')
    group.roles.add(editor_role, viewer_role)
    return group


@pytest.fixture
def editor_role_grant(db_setup, editor_role):
    """Create a role grant for editor on articles."""
    return RoleGrant.objects.create(
        role=editor_role,
        scope='articles',
        actions=['read', 'write'],
        context={}
    )


@pytest.fixture
def viewer_role_grant(db_setup, viewer_role):
    """Create a role grant for viewer on articles."""
    return RoleGrant.objects.create(
        role=viewer_role,
        scope='articles',
        actions=['read'],
        context={}
    )


# ── Actions expansion / collapse (named) ────────────────────────────

class TestActionsExpansion:
    """Test action expansion and collapse with named actions."""

    def test_expand_actions_basic(self):
        """Test basic action expansion with named actions."""
        # read has no implies → stays ['read']
        assert set(expand_actions('articles', ['read'])) == {'read'}
        # write implies read
        assert set(expand_actions('articles', ['write'])) == {'read', 'write'}
        # delete implies read, write → also pulls delete
        assert set(expand_actions('articles', ['delete'])) == {'delete', 'read', 'write'}
        # update implies read
        assert set(expand_actions('articles', ['update'])) == {'read', 'update'}

    def test_expand_actions_multi_level(self):
        """Test multi-level expansion."""
        # publish → write → read
        assert set(expand_actions('articles', ['publish'])) == {'publish', 'read', 'write'}
        # archive → publish → write → read
        assert set(expand_actions('articles', ['archive'])) == {'archive', 'publish', 'read', 'write'}

    def test_expand_actions_orders(self):
        """Test expansion on orders scope."""
        # approve → create
        assert set(expand_actions('orders', ['approve'])) == {'approve', 'create'}
        # refund → approve → create
        assert set(expand_actions('orders', ['refund'])) == {'approve', 'create', 'refund'}

    def test_collapse_actions(self):
        """Test action collapse to root actions."""
        assert collapse_actions('articles', ['read']) == {'read'}
        assert collapse_actions('articles', ['read', 'write']) == {'write'}
        assert collapse_actions('articles', ['read', 'write', 'delete']) == {'delete'}
        assert collapse_actions('articles', ['read', 'update']) == {'update'}
        assert collapse_actions('articles', ['publish', 'read', 'write']) == {'publish'}

    def test_collapse_actions_orders(self):
        """Test collapse on orders scope."""
        assert collapse_actions('orders', ['approve', 'create']) == {'approve'}
        assert collapse_actions('orders', ['refund', 'approve', 'create']) == {'refund'}

    def test_expand_unknown_action_noop(self):
        """Expanding an action not in the preset is a no-op."""
        assert set(expand_actions('articles', ['unknown'])) == {'unknown'}

    def test_get_valid_actions(self):
        """get_valid_actions returns the declared actions for a scope."""
        assert 'read' in get_valid_actions('articles')
        assert 'write' in get_valid_actions('articles')
        assert 'delete' in get_valid_actions('articles')
        assert 'publish' in get_valid_actions('articles')

    def test_get_implied_actions(self):
        """get_implied_actions returns the implied set."""
        assert get_implied_actions('articles', 'write') == {'read'}
        assert get_implied_actions('articles', 'read') == set()
        assert get_implied_actions('orders', 'approve') == {'create'}


class TestActionLabels:
    """Test action label functions."""

    def test_get_action_label_returns_label(self):
        """get_action_label returns the label when defined."""
        assert get_action_label('orders', 'create') == 'Create'
        assert get_action_label('orders', 'approve') == 'Approve'
        assert get_action_label('articles', 'publish') == 'Publish'

    def test_get_action_label_falls_back_to_key(self):
        """get_action_label returns the action key when no label is defined."""
        # If a scope has actions without labels, the key is returned
        # This tests the fallback behavior on an action that exists
        assert get_action_label('articles', 'read') == 'Read'

    def test_get_action_label_unknown_action(self):
        """get_action_label returns the key itself for unknown actions."""
        assert get_action_label('orders', 'nonexistent') == 'nonexistent'

    def test_get_scope_actions_labels(self):
        """get_scope_actions_labels returns all action→label mappings."""
        labels = get_scope_actions_labels('orders')
        assert labels['create'] == 'Create'
        assert labels['approve'] == 'Approve'
        assert labels['cancel'] == 'Cancel'
        assert labels['refund'] == 'Refund'


# ── Role assignment ──────────────────────────────────────────────────

class TestRoleAssignment:
    """Test role assignment with named actions."""

    def test_assign_role_creates_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test assign_role creates grants with expanded actions."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        grants = Grant.objects.filter(user=test_user, scope='articles')
        assert grants.count() == 1
        grant = grants.first()
        # write implies read, so grant should contain both
        assert 'read' in grant.actions
        assert 'write' in grant.actions

    def test_assign_role_not_found(self, test_user):
        """Test assign_role raises exception for non-existent role."""
        with pytest.raises(RoleNotFoundException):
            assign_role(test_user, 'nonexistent', 'articles')

    def test_revoke_role(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test revoke_role removes grants."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        count, _ = revoke_role(test_user, 'editor', 'articles')
        assert count > 0
        assert Grant.objects.filter(user=test_user, scope='articles').count() == 0

    def test_revoke_role_not_found(self, test_user):
        """Test revoke_role raises exception for non-existent role."""
        with pytest.raises(RoleNotFoundException):
            revoke_role(test_user, 'nonexistent', 'articles')


# ── Group assignment ─────────────────────────────────────────────────

class TestGroupAssignment:
    """Test group assignment with named actions."""

    def test_assign_group(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test assign_group creates UserGroup and grants."""
        ug = assign_group(test_user, 'staff', by=admin_user)
        assert ug is not None
        grants = Grant.objects.filter(user=test_user)
        assert grants.count() >= 2  # at least editor + viewer grants

    def test_assign_group_not_found(self, test_user):
        with pytest.raises(GroupNotFoundException):
            assign_group(test_user, 'nonexistent')

    def test_assign_group_already_assigned(self, test_user, staff_group, admin_user):
        assign_group(test_user, 'staff', by=admin_user)
        with pytest.raises(GroupAlreadyAssignedException):
            assign_group(test_user, 'staff', by=admin_user)

    def test_revoke_group(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test revoke_group removes UserGroup and grants."""
        assign_group(test_user, 'staff', by=admin_user)
        count, _ = revoke_group(test_user, 'staff')
        assert UserGroup.objects.filter(user=test_user).count() == 0


# ── Permission check ─────────────────────────────────────────────────

class TestPermissionCheck:
    """Test permission check with named actions."""

    def test_check_with_grant(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test check returns True when user has the required actions."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert check(test_user, 'articles', ['read']) is True
        assert check(test_user, 'articles', ['write']) is True
        assert check(test_user, 'articles', ['read', 'write']) is True  # AND

    def test_check_without_grant(self, test_user):
        """Test check returns False when user has no grant."""
        assert check(test_user, 'articles', ['read']) is False

    def test_check_and_logic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test AND logic: all actions must be present."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # User has read + write, but not delete
        assert check(test_user, 'articles', ['read', 'delete']) is False

    def test_check_with_context(self, test_user, editor_role, admin_user):
        """Test check with context filtering."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read', 'write'],
            context={'tenant_id': 42}
        )
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert check(test_user, 'articles', ['read'], tenant_id=42) is True
        assert check(test_user, 'articles', ['read'], tenant_id=99) is False

    def test_check_with_role_filter(self, test_user, editor_role, viewer_role, editor_role_grant, viewer_role_grant, admin_user):
        """Test check filtered by role."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # Has writethrough editor
        assert check(test_user, 'articles', ['read'], role='editor') is True
        # Does NOT have read through viewer (viewer not assigned)
        assert check(test_user, 'articles', ['read'], role='viewer') is False


# ── String check ─────────────────────────────────────────────────────

class TestStringCheck:
    """Test string-based permission check with named actions."""

    def test_str_check_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test str_check with AND format (default)."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert str_check(test_user, 'articles:read') is True
        assert str_check(test_user, 'articles:read/write') is True  # AND
        assert str_check(test_user, 'articles:read/write/delete') is False  # no delete

    def test_str_check_or_operator(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test str_check with | (OR) operator."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # User has read + write, so OR checks pass
        assert str_check(test_user, 'articles:read|write') is True
        assert str_check(test_user, 'articles:read|delete') is True  # has read
        assert str_check(test_user, 'articles:delete|publish') is False  # has neither

    def test_str_check_with_role(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test str_check with role filter."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert str_check(test_user, 'articles:read:editor') is True
        assert str_check(test_user, 'articles:read:viewer') is False

    def test_str_check_with_context(self, test_user, editor_role, admin_user):
        """Test str_check with query string context."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read', 'write'],
            context={'tenant_id': 42}
        )
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert str_check(test_user, 'articles:read?tenant_id=42') is True
        assert str_check(test_user, 'articles:read?tenant_id=99') is False

    def test_str_check_invalid_format(self, test_user):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            str_check(test_user, 'invalid')

    def test_str_check_mixed_separators_raises(self, test_user):
        """Test that mixed / and | raises ValueError."""
        with pytest.raises(ValueError, match="ambigu"):
            parse_permission('orders:create/approve|cancel')


# ── Grant override ───────────────────────────────────────────────────

class TestGrantOverride:
    """Test grant override with named actions."""

    def test_override_grant_sets_new_actions(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test override_grant replaces actions and locks the grant."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)

        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role)
        assert set(grant.actions) == {'read', 'write'}

        # Override to 'archive' only → should expand to archive/publish/read/write
        override_grant(test_user, 'articles', ['archive'])
        grant.refresh_from_db()
        assert grant.locked is True
        assert 'archive' in grant.actions
        assert 'read' in grant.actions  # implied

    def test_override_grant_with_empty_actions_deletes(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test override_grant with empty actions deletes the grant."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        override_grant(test_user, 'articles', [])
        assert Grant.objects.filter(user=test_user, scope='articles').count() == 0

    def test_override_grant_not_found(self, test_user):
        """Test override_grant raises when grant not found."""
        with pytest.raises(GrantNotFoundException):
            override_grant(test_user, 'articles', ['read'])


# ── Group sync ───────────────────────────────────────────────────────

class TestGroupSync:
    """Test group sync with named actions."""

    def test_group_sync_updates_grants(self, test_user, staff_group, editor_role, editor_role_grant, admin_user):
        """Test group_sync updates grants after RoleGrant change."""
        assign_group(test_user, 'staff', by=admin_user)

        # Modify role grant
        editor_role_grant.actions = ['read', 'write', 'delete']
        editor_role_grant.save()

        stats = group_sync('staff')
        assert stats['users_synced'] >= 1

        # Check grant was updated
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group__isnull=False)
        assert 'delete' in grant.actions

    def test_group_sync_preserves_overrides(self, test_user, staff_group, editor_role, editor_role_grant, admin_user):
        """Test group_sync does not touch locked grants."""
        assign_group(test_user, 'staff', by=admin_user)

        # Lock a grant
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role)
        grant.locked = True
        grant.actions = ['read']  # custom
        grant.save()

        # Modify role grant
        editor_role_grant.actions = ['read', 'write', 'delete']
        editor_role_grant.save()

        group_sync('staff')

        grant.refresh_from_db()
        assert set(grant.actions) == {'read'}  # unchanged

    def test_group_sync_with_scope_filter(self, test_user, staff_group, editor_role, editor_role_grant, admin_user):
        """Test group_sync with scope parameter."""
        assign_group(test_user, 'staff', by=admin_user)

        # Create another grant for comments scope
        viewer_role = Role.objects.get(slug='viewer')
        RoleGrant.objects.create(
            role=viewer_role,
            scope='comments',
            actions=['read'],
            context={}
        )
        # Re-assign group to pick up new grant
        revoke_group(test_user, 'staff')
        assign_group(test_user, 'staff', by=admin_user)

        # Modify editor grant
        editor_role_grant.actions = ['read', 'write', 'delete']
        editor_role_grant.save()

        # Sync only articles
        group_sync('staff', scope='articles')

        # Articles grant updated
        articles_grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role)
        assert 'delete' in articles_grant.actions

    def test_group_sync_with_role_filter(self, test_user, staff_group, editor_role, editor_role_grant, admin_user):
        """Test group_sync with role_slugs parameter."""
        assign_group(test_user, 'staff', by=admin_user)

        editor_role_grant.actions = ['read', 'write', 'delete']
        editor_role_grant.save()

        stats = group_sync('staff', role_slugs=['editor'])
        assert stats['users_synced'] >= 1


# ── ScopePermission ──────────────────────────────────────────────────

class TestScopePermission:
    """Test ScopePermission class with named actions."""

    def test_scope_permission_and(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test ScopePermission with AND (/) separator."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)

        perm = ScopePermission('articles:read/write')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True

        perm2 = ScopePermission('articles:read/write/delete')
        assert perm2.has_permission(request, Mock()) is False

    def test_scope_permission_or(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test ScopePermission with OR (|) separator."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)

        perm = ScopePermission('articles:read|delete')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True  # has read

        perm2 = ScopePermission('articles:delete|publish')
        assert perm2.has_permission(request, Mock()) is False  # has neither

    def test_scope_permission_with_context(self, test_user, editor_role, admin_user):
        """Test ScopePermission with context."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read', 'write'],
            context={'tenant_id': 42}
        )
        assign_role(test_user, 'editor', 'articles', by=admin_user)

        perm = ScopePermission('articles:read')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True

        perm_ctx = ScopePermission('articles:read?tenant_id=99')
        assert perm_ctx.has_permission(request, Mock()) is False


# ── Access manager ───────────────────────────────────────────────────

class TestAccessManager:
    """Test access_manager factory with named actions."""

    def test_access_manager_basic(self, test_user, admin_user):
        """Test access_manager creates correct ScopePermission."""
        perm = access_manager('read')
        assert isinstance(perm, ScopePermission)
        assert perm.perm == 'access:read:manager'

    def test_access_manager_and(self):
        """Test access_manager with AND actions."""
        perm = access_manager('read/write')
        assert perm.perm == 'access:read/write:manager'

    def test_access_manager_or(self):
        """Test access_manager with OR actions."""
        perm = access_manager('read|write')
        assert perm.perm == 'access:read|write:manager'

    def test_access_manager_without_role(self, settings):
        """Test access_manager when role is None."""
        settings.ACCESS_MANAGER_ROLE = None
        perm = access_manager('read')
        assert perm.perm == 'access:read'

    def test_access_manager_with_context(self, settings):
        """Test access_manager with context."""
        settings.ACCESS_MANAGER_CONTEXT = {'app': 'crm'}
        perm = access_manager('read')
        assert perm.ctx == {'app': 'crm'}

    def test_access_manager_missing_scope(self, settings):
        """Test access_manager uses default 'access' when scope is missing."""
        delattr(settings, 'ACCESS_MANAGER_SCOPE')
        settings.ACCESS_MANAGER_ROLE = None
        perm = access_manager('read')
        assert perm.perm == 'access:read'  # defaults to 'access', no role


# ── Parse permission ─────────────────────────────────────────────────

class TestParsePermission:
    """Test parse_permission with named actions."""

    def test_parse_single_action(self):
        """Test parsing single action."""
        scope, actions, operator, role, context = parse_permission('articles:read')
        assert scope == 'articles'
        assert actions == ['read']
        assert operator == '&'
        assert role is None
        assert context == {}

    def test_parse_and_actions(self):
        """Test parsing AND (/)."""
        scope, actions, operator, role, context = parse_permission('orders:create/approve/cancel')
        assert scope == 'orders'
        assert actions == ['create', 'approve', 'cancel']
        assert operator == '&'
        assert role is None

    def test_parse_or_actions(self):
        """Test parsing OR (|)."""
        scope, actions, operator, role, context = parse_permission('orders:create|approve|cancel')
        assert scope == 'orders'
        assert actions == ['create', 'approve', 'cancel']
        assert operator == '|'
        assert role is None

    def test_parse_with_role(self):
        """Test parsing with role."""
        scope, actions, operator, role, context = parse_permission('articles:read/write:editor')
        assert scope == 'articles'
        assert actions == ['read', 'write']
        assert operator == '&'
        assert role == 'editor'

    def test_parse_or_with_role(self):
        """Test parsing OR with role."""
        scope, actions, operator, role, context = parse_permission('articles:read|write:editor')
        assert scope == 'articles'
        assert actions == ['read', 'write']
        assert operator == '|'
        assert role == 'editor'

    def test_parse_with_context(self):
        """Test parsing with context."""
        scope, actions, operator, role, context = parse_permission(
            'articles:read/write?tenant_id=42&status=active'
        )
        assert scope == 'articles'
        assert actions == ['read', 'write']
        assert operator == '&'
        assert role is None
        assert context == {'tenant_id': 42, 'status': 'active'}

    def test_parse_with_role_and_context(self):
        """Test parsing with role and context."""
        scope, actions, operator, role, context = parse_permission(
            'articles:read/write:editor?tenant_id=42'
        )
        assert scope == 'articles'
        assert actions == ['read', 'write']
        assert operator == '&'
        assert role == 'editor'
        assert context == {'tenant_id': 42}

    def test_parse_invalid_format(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Format de permission invalide"):
            parse_permission('invalid')

    def test_parse_mixed_separators_raises(self):
        """Test mixed / and | raises."""
        with pytest.raises(ValueError, match="ambigu"):
            parse_permission('orders:create/approve|cancel')


# ── Any action check ─────────────────────────────────────────────────

class TestAnyActionCheck:
    """Test any_action_check with named actions."""

    def test_any_action_check_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test OR check on same scope."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # User has read + write
        assert any_action_check(test_user, 'articles', ['read']) is True
        assert any_action_check(test_user, 'articles', ['read', 'delete']) is True  # has read
        assert any_action_check(test_user, 'articles', ['delete', 'publish']) is False  # has neither

    def test_any_action_check_with_role(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test OR check filtered by role."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert any_action_check(test_user, 'articles', ['read', 'delete'], role='editor') is True
        assert any_action_check(test_user, 'articles', ['read', 'delete'], role='viewer') is False

    def test_any_action_check_with_context(self, test_user, editor_role, admin_user):
        """Test OR check with context."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read', 'write'],
            context={'tenant_id': 42}
        )
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert any_action_check(test_user, 'articles', ['read'], tenant_id=42) is True
        assert any_action_check(test_user, 'articles', ['read'], tenant_id=99) is False


# ── Any permission check ─────────────────────────────────────────────

class TestAnyPermissionCheck:
    """Test any_permission_check with named actions."""

    def test_any_permission_check_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test OR across different permission strings."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert any_permission_check(test_user, 'articles:read') is True
        assert any_permission_check(test_user, 'articles:delete', 'articles:read') is True  # has read
        assert any_permission_check(test_user, 'articles:delete', 'articles:publish') is False

    def test_any_permission_check_mixed_operators(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test AND within one perm, OR across perms."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # articles:read/write = AND (must have both) → True
        # articles:delete/publish = AND (must have both) → False
        # overall OR → True
        assert any_permission_check(test_user, 'articles:read/write', 'articles:delete/publish') is True

    def test_any_permission_check_with_roles(self, test_user, editor_role, viewer_role, editor_role_grant, admin_user):
        """Test OR check with role filters."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert any_permission_check(
            test_user,
            'articles:read:editor',
            'articles:read:viewer'
        ) is True

    def test_any_permission_check_with_context(self, test_user, editor_role, admin_user):
        """Test OR check with context."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read', 'write'],
            context={'tenant_id': 42}
        )
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert any_permission_check(
            test_user,
            'articles:read?tenant_id=42',
            'articles:read?tenant_id=99'
        ) is True  # first matches

    def test_any_permission_check_empty(self, test_user):
        """Test empty perms returns False."""
        assert any_permission_check(test_user) is False


# ── ScopeAnyActionPermission ─────────────────────────────────────────

class TestScopeAnyActionPermission:
    """Test ScopeAnyActionPermission (always OR)."""

    def test_scope_any_action_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test always-OR on same scope."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyActionPermission('articles:read/delete')
        request = Mock(user=test_user)
        # Even with '/', this class forces OR → True (has read)
        assert perm.has_permission(request, Mock()) is True

    def test_scope_any_action_fails(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test always-OR fails when user has none."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyActionPermission('articles:delete/publish')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is False

    def test_scope_any_action_with_role(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test always-OR with role filter."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyActionPermission('articles:read/delete:editor')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True

    def test_scope_any_action_validation(self):
        """Test validation on empty string."""
        with pytest.raises(ValueError):
            ScopeAnyActionPermission('')


# ── ScopeAnyPermission ───────────────────────────────────────────────

class TestScopeAnyPermission:
    """Test ScopeAnyPermission with named actions."""

    def test_scope_any_permission_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test OR across multiple permission strings."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyPermission('articles:delete', 'articles:read')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True

    def test_scope_any_permission_fails(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test fails when none match."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyPermission('articles:delete', 'articles:publish')
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is False

    def test_scope_any_permission_with_roles(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test with role filters."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        perm = ScopeAnyPermission(
            'articles:read:editor',
            'articles:write:viewer'
        )
        request = Mock(user=test_user)
        assert perm.has_permission(request, Mock()) is True

    def test_scope_any_permission_validation(self):
        """Test validation on empty args."""
        with pytest.raises(ValueError):
            ScopeAnyPermission()


# ── Activate / Deactivate ────────────────────────────────────────────

class TestActivateDeactivatePermissions:
    """Test activate/deactivate with named actions."""

    def test_activate_all_user_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        # Deactivate first
        Grant.objects.filter(user=test_user).update(is_active=False)
        activate_user_permissions(test_user)
        assert Grant.objects.filter(user=test_user, is_active=True).exists()

    def test_deactivate_all_user_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        deactivate_user_permissions(test_user)
        assert not Grant.objects.filter(user=test_user, is_active=True).exists()

    def test_activate_by_scope(self, test_user, editor_role, editor_role_grant, admin_user):
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        Grant.objects.filter(user=test_user).update(is_active=False)
        activate_user_permissions(test_user, scope='articles')
        assert Grant.objects.filter(user=test_user, scope='articles', is_active=True).exists()

    def test_deactivate_by_scope(self, test_user, editor_role, editor_role_grant, admin_user):
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        deactivate_user_permissions(test_user, scope='articles')
        assert not Grant.objects.filter(user=test_user, scope='articles', is_active=True).exists()

    def test_reactivate_restores_check(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test that reactivating grants restores permission checks."""
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assert check(test_user, 'articles', ['read']) is True
        deactivate_user_permissions(test_user)
        assert check(test_user, 'articles', ['read']) is False
        activate_user_permissions(test_user)
        assert check(test_user, 'articles', ['read']) is True


# ── Extra permissions ────────────────────────────────────────────────

class TestExtraPermissions:
    """Test extra_permissions with named actions."""

    def test_returns_empty_list_when_not_configured(self):
        assert extra_permissions() == []

    @override_settings(EXTRA_PERMISSIONS=[])
    def test_returns_empty_list_when_configured_empty(self):
        assert extra_permissions() == []

    @override_settings(
        EXTRA_PERMISSIONS=['oxutils.permissions.perms.ScopePermission']
    )
    def test_imports_and_returns_instances(self, settings):
        # Clear cache
        extra_permissions.cache_clear()
        result = extra_permissions()
        assert len(result) == 1
        # import_string returns the class itself, not an instance
        from ninja_extra.permissions import BasePermission
        assert issubclass(result[0], BasePermission)

    @override_settings(EXTRA_PERMISSIONS=['nonexistent.Path'])
    def test_raises_on_bad_path(self):
        extra_permissions.cache_clear()
        with pytest.raises(ImproperlyConfigured):
            extra_permissions()

    @override_settings(EXTRA_PERMISSIONS=42)
    def test_raises_on_non_list(self):
        extra_permissions.cache_clear()
        with pytest.raises(ImproperlyConfigured):
            extra_permissions()


# ── Models ───────────────────────────────────────────────────────────

class TestModels:
    """Test models with named actions."""

    def test_role_creation(self, db_setup):
        role = Role.objects.create(slug='test_role', name='Test Role')
        assert str(role) == 'test_role'

    def test_group_creation(self, db_setup, editor_role):
        group = Group.objects.create(slug='test_group', name='Test Group')
        group.roles.add(editor_role)
        # save() preserves the explicitly provided slug (no longer overwrites)
        assert str(group) == 'test_group'

    def test_role_grant_clean_expands(self, db_setup, editor_role):
        """Test RoleGrant.clean() expands actions based on hierarchy."""
        rg = RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['write'],  # write implies read
            context={}
        )
        assert set(rg.actions) == {'read', 'write'}

    def test_role_grant_expand_archive(self, db_setup, editor_role):
        """Test deep expansion."""
        rg = RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['archive'],  # archive → publish → write → read
            context={}
        )
        assert 'archive' in rg.actions
        assert 'publish' in rg.actions
        assert 'write' in rg.actions
        assert 'read' in rg.actions

    def test_grant_unique_constraint(self, test_user, editor_role, db_setup):
        """Test unique constraint on grants."""
        rg = RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['read'],
            context={}
        )
        Grant.objects.create(
            user=test_user,
            scope='articles',
            role=editor_role,
            actions=['read'],
        )
        with pytest.raises(Exception):
            Grant.objects.create(
                user=test_user,
                scope='articles',
                role=editor_role,
                actions=['read'],
            )


# ── Preset discovery helpers ─────────────────────────────────────────

def _fake_app_config(label, module_attrs):
    """Return an object that looks like a Django AppConfig."""
    return type("FakeConfig", (), {"label": label, "name": f"fake_{label}"})


def _patch_get_app_configs(monkeypatch, configs):
    """Mock `apps.get_app_configs` to return *configs*."""
    monkeypatch.setattr("django.apps.apps.get_app_configs", lambda: configs)


def _patch_import_module(monkeypatch, module_map):
    """
    Monkeypatch `importlib.import_module` so that for each app label
    we return a fake module with the given attributes.
    """
    import importlib
    orig = importlib.import_module

    def _import(modname):
        for label, attrs in module_map.items():
            if modname == f"fake_{label}.permissions":
                mod = Mock()
                for k, v in attrs.items():
                    setattr(mod, k, v)
                return mod
        return orig(modname)

    monkeypatch.setattr(importlib, "import_module", _import)


class TestDiscoverAppPresets:
    """Test discover_app_presets with named actions."""

    def test_discovers_preset_from_app(self, monkeypatch):
        config = _fake_app_config("myapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {
            "myapp": {
                "PERMISSION_PRESET": {
                    "roles": [{"slug": "editor", "name": "Editor"}],
                    "groups": [],
                    "role_grants": [],
                }
            }
        })
        presets = presets_mod.discover_app_presets()
        assert len(presets) >= 1
        assert presets[0]["roles"][0]["slug"] == "editor"

    def test_preset_includes_actions(self, monkeypatch):
        """Test that actions are discovered."""
        config = _fake_app_config("myapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {
            "myapp": {
                "PERMISSION_PRESET": {
                    "actions": {
                        "orders": {
                            "create": {"implies": []},
                            "ship": {"implies": ["create"]},
                        }
                    },
                    "roles": [],
                    "groups": [],
                    "role_grants": [],
                }
            }
        })
        presets = presets_mod.discover_app_presets()
        assert "actions" in presets[0]
        assert "orders" in presets[0]["actions"]

    def test_app_without_permissions_module_is_skipped(self, monkeypatch):
        config = _fake_app_config("noapp", {})
        _patch_get_app_configs(monkeypatch, [config])

        import importlib
        orig = importlib.import_module

        def _import(modname):
            if modname == "fake_noapp.permissions":
                raise ModuleNotFoundError()
            return orig(modname)

        monkeypatch.setattr(importlib, "import_module", _import)
        presets = presets_mod.discover_app_presets()
        assert presets == []

    def test_app_without_preset_is_skipped(self, monkeypatch):
        config = _fake_app_config("noapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {"noapp": {}})
        presets = presets_mod.discover_app_presets()
        assert presets == []


class TestDiscoverAccessScopes:
    """Test discover_access_scopes."""

    def test_discovers_scopes_from_app(self, monkeypatch):
        config = _fake_app_config("myapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {
            "myapp": {"ACCESS_SCOPES": ["orders", "invoices"]}
        })
        scopes = presets_mod.discover_access_scopes()
        keys = {s["key"] for s in scopes}
        assert "orders" in keys
        assert "invoices" in keys

    def test_discovers_scopes_with_labels(self, monkeypatch):
        """ACCESS_SCOPES can be a list of dicts with key and label."""
        config = _fake_app_config("myapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {
            "myapp": {"ACCESS_SCOPES": [
                {"key": "orders", "label": "Orders"},
            ]}
        })
        scopes = presets_mod.discover_access_scopes()
        assert len(scopes) == 1
        assert scopes[0]["key"] == "orders"
        assert scopes[0]["label"] == "Orders"

    def test_deduplicates(self, monkeypatch):
        c1 = _fake_app_config("a", {})
        c2 = _fake_app_config("b", {})
        _patch_get_app_configs(monkeypatch, [c1, c2])
        _patch_import_module(monkeypatch, {
            "a": {"ACCESS_SCOPES": ["orders"]},
            "b": {"ACCESS_SCOPES": ["orders"]},
        })
        scopes = presets_mod.discover_access_scopes()
        keys = [s["key"] for s in scopes]
        assert keys.count("orders") == 1


class TestRegisterPreset:
    """Test register_preset with actions."""

    def test_extends_base_with_discovered(self, monkeypatch):
        config = _fake_app_config("myapp", {})
        _patch_get_app_configs(monkeypatch, [config])
        _patch_import_module(monkeypatch, {
            "myapp": {
                "PERMISSION_PRESET": {
                    "actions": {
                        "orders": {
                            "create": {"implies": []},
                        }
                    },
                    "roles": [{"slug": "editor", "name": "Editor"}],
                    "groups": [],
                    "role_grants": [],
                }
            }
        })
        base = {"roles": [], "groups": [], "role_grants": [], "actions": {}}
        result = presets_mod.register_preset(base)
        assert len(result["roles"]) >= 1
        assert "orders" in result["actions"]

    def test_different_scopes_from_multiple_apps_ok(self, monkeypatch):
        """Different scopes from different apps are fine."""
        c1 = _fake_app_config("a", {})
        c2 = _fake_app_config("b", {})
        _patch_get_app_configs(monkeypatch, [c1, c2])
        _patch_import_module(monkeypatch, {
            "a": {
                "PERMISSION_PRESET": {
                    "actions": {"scope_a": {"read": {"implies": []}}},
                    "roles": [], "groups": [], "role_grants": [],
                }
            },
            "b": {
                "PERMISSION_PRESET": {
                    "actions": {"scope_b": {"read": {"implies": []}}},
                    "roles": [], "groups": [], "role_grants": [],
                }
            },
        })
        base = {"roles": [], "groups": [], "role_grants": [], "actions": {}}
        result = presets_mod.register_preset(base)
        assert "scope_a" in result["actions"]
        assert "scope_b" in result["actions"]

    def test_duplicate_scope_raises_error(self, monkeypatch):
        """Two apps defining the same scope raises ImproperlyConfigured."""
        c1 = _fake_app_config("orders", {})
        c2 = _fake_app_config("payments", {})
        _patch_get_app_configs(monkeypatch, [c1, c2])
        _patch_import_module(monkeypatch, {
            "orders": {
                "PERMISSION_PRESET": {
                    "actions": {"orders": {"create": {"implies": []}}},
                    "roles": [], "groups": [], "role_grants": [],
                }
            },
            "payments": {
                "PERMISSION_PRESET": {
                    "actions": {"orders": {"refund": {"implies": ["create"]}}},
                    "roles": [], "groups": [], "role_grants": [],
                }
            },
        })
        base = {"roles": [], "groups": [], "role_grants": [], "actions": {}}
        with pytest.raises(ImproperlyConfigured, match="already owned"):
            presets_mod.register_preset(base)

    def test_duplicate_scope_with_base_preset_raises_error(self, monkeypatch):
        """App defining a scope already in the base preset raises error."""
        c1 = _fake_app_config("orders", {})
        _patch_get_app_configs(monkeypatch, [c1])
        _patch_import_module(monkeypatch, {
            "orders": {
                "PERMISSION_PRESET": {
                    "actions": {"orders": {"create": {"implies": []}}},
                    "roles": [], "groups": [], "role_grants": [],
                }
            },
        })
        base = {
            "roles": [], "groups": [], "role_grants": [],
            "actions": {"orders": {"read": {"implies": []}}},
        }
        with pytest.raises(ImproperlyConfigured, match="already owned"):
            presets_mod.register_preset(base)
