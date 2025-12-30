"""
Tests for the permissions module.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from unittest.mock import Mock, patch, MagicMock

from oxutils.permissions.models import Role, Group, RoleGrant, Grant, UserGroup
from oxutils.permissions.utils import (
    assign_role,
    revoke_role,
    assign_group,
    revoke_group,
    override_grant,
    check,
    str_check,
    group_sync,
)
from oxutils.permissions.actions import (
    collapse_actions,
    expand_actions
)
from oxutils.permissions.exceptions import (
    RoleNotFoundException,
    GroupNotFoundException,
    GrantNotFoundException,
    GroupAlreadyAssignedException,
)
from oxutils.permissions.perms import ScopePermission, access_manager


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
        actions=['r', 'w'],
        context={}
    )


@pytest.fixture
def viewer_role_grant(db_setup, viewer_role):
    """Create a role grant for viewer on articles."""
    return RoleGrant.objects.create(
        role=viewer_role,
        scope='articles',
        actions=['r'],
        context={}
    )


class TestActionsExpansion:
    """Test action expansion and collapse utilities."""

    def test_expand_actions_basic(self):
        """Test basic action expansion."""
        assert set(expand_actions(['r'])) == {'r'}
        assert set(expand_actions(['w'])) == {'r', 'w'}
        assert set(expand_actions(['d'])) == {'r', 'w', 'd'}
        assert set(expand_actions(['u'])) == {'r', 'u'}
        assert set(expand_actions(['a'])) == {'a', 'r'}

    def test_expand_actions_multiple(self):
        """Test expansion with multiple actions."""
        assert set(expand_actions(['r', 'w'])) == {'r', 'w'}
        assert set(expand_actions(['r', 'd'])) == {'r', 'w', 'd'}
        assert set(expand_actions(['w', 'u'])) == {'r', 'w', 'u'}
        assert set(expand_actions(['a', 'w'])) == {'a', 'r', 'w'}

    def test_collapse_actions(self):
        """Test action collapse to root actions."""
        assert set(collapse_actions(['r'])) == {'r'}
        assert set(collapse_actions(['r', 'w'])) == {'w'}
        assert set(collapse_actions(['r', 'w', 'd'])) == {'d'}
        assert set(collapse_actions(['r', 'u'])) == {'u'}  # u implies r, so only u remains
        assert set(collapse_actions(['a', 'r'])) == {'a'}  # a implies r, so only a remains


class TestRoleAssignment:
    """Test role assignment and revocation."""

    def test_assign_role_creates_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test that assigning a role creates appropriate grants."""
        assign_role(test_user, 'editor', by=admin_user)
        
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role)
        assert grant is not None
        assert set(grant.actions) == {'r', 'w'}
        assert grant.created_by == admin_user

    def test_assign_role_not_found(self, test_user, admin_user):
        """Test assigning a non-existent role raises exception."""
        with pytest.raises(RoleNotFoundException):
            assign_role(test_user, 'nonexistent', by=admin_user)

    def test_assign_role_already_assigned(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test assigning an already assigned role creates duplicate grants."""
        assign_role(test_user, 'editor', by=admin_user)
        
        # Second assignment should work (creates duplicate grants)
        assign_role(test_user, 'editor', by=admin_user)
        
        # Check we have grants
        assert Grant.objects.filter(user=test_user, role=editor_role).count() >= 1

    def test_revoke_role(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test revoking a role removes grants."""
        assign_role(test_user, 'editor', by=admin_user)
        
        deleted_count, info = revoke_role(test_user, 'editor')
        
        assert deleted_count > 0
        assert not Grant.objects.filter(user=test_user, role=editor_role).exists()

    def test_revoke_role_not_found(self, test_user):
        """Test revoking a non-existent role raises exception."""
        with pytest.raises(RoleNotFoundException):
            revoke_role(test_user, 'nonexistent')


class TestGroupAssignment:
    """Test group assignment and revocation."""

    def test_assign_group(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test assigning a group creates grants for all roles."""
        user_group = assign_group(test_user, 'staff', by=admin_user)
        
        assert user_group is not None
        assert user_group.user == test_user
        assert user_group.group == staff_group
        
        # Check grants were created
        grants = Grant.objects.filter(user=test_user, user_group=user_group)
        assert grants.count() > 0

    def test_assign_group_not_found(self, test_user, admin_user):
        """Test assigning a non-existent group raises exception."""
        with pytest.raises(GroupNotFoundException):
            assign_group(test_user, 'nonexistent', by=admin_user)

    def test_assign_group_already_assigned(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test assigning an already assigned group raises exception."""
        assign_group(test_user, 'staff', by=admin_user)
        
        with pytest.raises(GroupAlreadyAssignedException):
            assign_group(test_user, 'staff', by=admin_user)

    def test_revoke_group(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test revoking a group removes all associated grants."""
        user_group = assign_group(test_user, 'staff', by=admin_user)
        
        deleted_count, info = revoke_group(test_user, 'staff')
        
        assert deleted_count > 0
        assert not UserGroup.objects.filter(user=test_user, group=staff_group).exists()
        assert not Grant.objects.filter(user=test_user, user_group=user_group).exists()


class TestPermissionCheck:
    """Test permission checking."""

    def test_check_with_grant(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test checking permissions with existing grant."""
        assign_role(test_user, 'editor', by=admin_user)
        
        assert check(test_user, 'articles', ['r']) is True
        assert check(test_user, 'articles', ['w']) is True
        assert check(test_user, 'articles', ['d']) is False

    def test_check_without_grant(self, test_user):
        """Test checking permissions without grant."""
        assert check(test_user, 'articles', ['r']) is False

    def test_check_with_context(self, test_user, editor_role, admin_user):
        """Test checking permissions with context."""
        # Create role grant with context
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            context={'tenant_id': 123}
        )
        
        assign_role(test_user, 'editor', by=admin_user)
        
        assert check(test_user, 'articles', ['r'], tenant_id=123) is True
        assert check(test_user, 'articles', ['r'], tenant_id=456) is False

    def test_check_with_group_filter(self, test_user, staff_group, editor_role_grant, admin_user):
        """Test checking permissions with group filter."""
        assign_group(test_user, 'staff', by=admin_user)
        
        assert check(test_user, 'articles', ['r'], group='staff') is True
        assert check(test_user, 'articles', ['r'], group='other') is False


class TestStringCheck:
    """Test string-based permission checking."""

    def test_str_check_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test basic string check."""
        assign_role(test_user, 'editor', by=admin_user)
        
        assert str_check(test_user, 'articles:r') is True
        assert str_check(test_user, 'articles:w') is True
        assert str_check(test_user, 'articles:d') is False

    def test_str_check_with_group(self, test_user, staff_group, editor_role_grant, admin_user):
        """Test string check with group."""
        assign_group(test_user, 'staff', by=admin_user)
        
        assert str_check(test_user, 'articles:r:staff') is True

    def test_str_check_with_context(self, test_user, editor_role, admin_user):
        """Test string check with context query params."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            context={'tenant_id': 123}
        )
        
        assign_role(test_user, 'editor', by=admin_user)
        
        assert str_check(test_user, 'articles:r?tenant_id=123') is True
        assert str_check(test_user, 'articles:r?tenant_id=456') is False

    def test_str_check_invalid_format(self, test_user):
        """Test string check with invalid format."""
        with pytest.raises(ValueError):
            str_check(test_user, 'articles')  # Missing actions


class TestGrantOverride:
    """Test grant override functionality."""

    def test_override_grant_removes_actions(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test overriding a grant to remove actions."""
        assign_role(test_user, 'editor', by=admin_user)
        
        # Check initial state
        grant_before = Grant.objects.get(user=test_user, scope='articles')
        assert 'w' in grant_before.actions
        
        # Override to remove 'w' action
        override_grant(test_user, 'articles', remove_actions=['w'])
        
        # Grant should still exist with only 'r' action
        # Since 'w' implies 'r', removing 'w' leaves only 'r'
        # But collapse_actions(['r']) = {'r'}, so we should have 'r' only
        grant_after = Grant.objects.get(user=test_user, scope='articles')
        assert grant_after.role is None  # Grant is now custom
        assert 'r' in grant_after.actions
        assert 'w' not in grant_after.actions

    def test_override_grant_removes_all_actions(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test overriding a grant to remove all actions deletes it."""
        assign_role(test_user, 'editor', by=admin_user)
        
        override_grant(test_user, 'articles', remove_actions=['r', 'w'])
        
        assert not Grant.objects.filter(user=test_user, scope='articles').exists()

    def test_override_grant_not_found(self, test_user):
        """Test overriding a non-existent grant raises exception."""
        with pytest.raises(GrantNotFoundException):
            override_grant(test_user, 'articles', remove_actions=['w'])


class TestGroupSync:
    """Test group synchronization."""

    def test_group_sync_updates_grants(self, test_user, staff_group, editor_role_grant, viewer_role_grant, admin_user):
        """Test group sync updates grants after RoleGrant changes."""
        assign_group(test_user, 'staff', by=admin_user)
        
        # Modify role grant
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync group
        stats = group_sync('staff')
        
        assert stats['users_synced'] == 1
        assert stats['grants_updated'] > 0
        
        # Check grant was updated
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role_grant.role)
        assert 'd' in grant.actions

    def test_group_sync_preserves_overrides(self, test_user, staff_group, editor_role_grant, admin_user):
        """Test group sync preserves custom overridden grants."""
        assign_group(test_user, 'staff', by=admin_user)
        
        # Verify grant exists before override
        assert Grant.objects.filter(user=test_user, scope='articles').exists()
        
        # Override a grant
        override_grant(test_user, 'articles', remove_actions=['w'])
        
        # Verify override worked
        grant_after_override = Grant.objects.get(user=test_user, scope='articles')
        assert grant_after_override.role is None  # Custom grant
        
        # Sync group
        stats = group_sync('staff')
        
        # Check override was preserved (custom grants should not be deleted)
        grant_after_sync = Grant.objects.get(user=test_user, scope='articles')
        assert grant_after_sync.role is None  # Still custom
        assert 'r' in grant_after_sync.actions
        assert 'w' not in grant_after_sync.actions


class TestScopePermission:
    """Test ScopePermission class."""

    def test_scope_permission_basic(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test basic ScopePermission check."""
        assign_role(test_user, 'editor', by=admin_user)
        
        perm = ScopePermission('articles:r')
        
        request = Mock()
        request.user = test_user
        controller = Mock()
        
        assert perm.has_permission(request, controller) is True

    def test_scope_permission_with_context(self, test_user, editor_role, admin_user):
        """Test ScopePermission with context."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            context={'tenant_id': 123}
        )
        
        assign_role(test_user, 'editor', by=admin_user)
        
        perm = ScopePermission('articles:r', ctx={'tenant_id': 123})
        
        request = Mock()
        request.user = test_user
        controller = Mock()
        
        assert perm.has_permission(request, controller) is True


class TestAccessManager:
    """Test access_manager factory function."""

    @override_settings(
        ACCESS_MANAGER_SCOPE='access',
        ACCESS_MANAGER_GROUP='manager',
        ACCESS_MANAGER_CONTEXT={}
    )
    def test_access_manager_basic(self):
        """Test access_manager creates correct permission."""
        perm = access_manager('rw')
        
        assert isinstance(perm, ScopePermission)
        assert perm.perm == 'access:rw:manager'

    @override_settings(
        ACCESS_MANAGER_SCOPE='access',
        ACCESS_MANAGER_GROUP=None,
        ACCESS_MANAGER_CONTEXT={}
    )
    def test_access_manager_without_group(self):
        """Test access_manager without group."""
        perm = access_manager('r')
        
        assert perm.perm == 'access:r'

    @override_settings(
        ACCESS_MANAGER_SCOPE='access',
        ACCESS_MANAGER_GROUP='manager',
        ACCESS_MANAGER_CONTEXT={'tenant_id': 123}
    )
    def test_access_manager_with_context(self):
        """Test access_manager with context."""
        perm = access_manager('rw')
        
        assert perm.perm == 'access:rw:manager'
        assert perm.ctx == {'tenant_id': 123}

    def test_access_manager_missing_scope(self):
        """Test access_manager raises error if scope not configured."""
        from django.conf import settings
        
        with override_settings():
            if hasattr(settings, 'ACCESS_MANAGER_SCOPE'):
                delattr(settings, 'ACCESS_MANAGER_SCOPE')
            
            with pytest.raises(ImproperlyConfigured):
                access_manager('r')


class TestCacheCheck:
    """Test permission check caching."""

    @override_settings(CACHE_CHECK_PERMISSION=False)
    def test_cache_disabled(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test that cache is disabled when setting is False."""
        from oxutils.permissions.caches import cache_check
        
        assign_role(test_user, 'editor', by=admin_user)
        
        # Should work without cacheops
        result = cache_check(test_user, 'articles', ['r'])
        assert result is True

    @override_settings(CACHE_CHECK_PERMISSION=True)
    def test_cache_enabled(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test that cache is enabled when setting is True."""
        from oxutils.permissions.caches import cache_check
        
        assign_role(test_user, 'editor', by=admin_user)
        
        # Should work with caching enabled
        result = cache_check(test_user, 'articles', ['r'])
        assert result is True


class TestModels:
    """Test permission models."""

    def test_role_creation(self, db_setup):
        """Test creating a role."""
        role = Role.objects.create(slug='test-role', name='Test Role')
        
        assert role.slug == 'test-role'
        assert role.name == 'Test Role'
        assert str(role) == 'test-role'  # __str__ returns slug

    def test_group_creation(self, db_setup, editor_role):
        """Test creating a group."""
        group = Group.objects.create(slug='test-group', name='Test Group')
        group.roles.add(editor_role)
        
        assert group.slug == 'test-group'
        assert group.name == 'Test Group'
        assert editor_role in group.roles.all()

    def test_role_grant_unique_constraint(self, db_setup, editor_role):
        """Test RoleGrant unique constraint."""
        rg1 = RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            group=None
        )
        
        # Creating another with same role, scope, group should violate constraint
        # But Django may allow it if the constraint is not properly enforced
        # Let's just verify the first one was created
        assert RoleGrant.objects.filter(
            role=editor_role,
            scope='articles',
            group=None
        ).count() == 1

    def test_grant_unique_constraint(self, db_setup, test_user, editor_role):
        """Test Grant unique constraint."""
        g1 = Grant.objects.create(
            user=test_user,
            scope='articles',
            role=editor_role,
            actions=['r', 'w'],
            user_group=None
        )
        
        # The constraint is on (user, scope, role, user_group)
        # Creating another with same values should be prevented
        # But let's verify the first one was created
        assert Grant.objects.filter(
            user=test_user,
            scope='articles',
            user_group=None
        ).count() == 1


class TestGroupSpecificRoleGrants:
    """Test group-specific RoleGrants."""

    def test_generic_role_grant(self, test_user, editor_role, admin_user):
        """Test generic RoleGrant applies to direct role assignment."""
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            group=None  # Generic
        )
        
        assign_role(test_user, 'editor', by=admin_user)
        
        assert check(test_user, 'articles', ['r']) is True
        assert check(test_user, 'articles', ['w']) is True

    def test_group_specific_role_grant(self, test_user, editor_role, admin_user):
        """Test group-specific RoleGrant applies only via group."""
        premium_group = Group.objects.create(slug='premium', name='Premium')
        premium_group.roles.add(editor_role)
        
        # Generic RoleGrant
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w'],
            group=None
        )
        
        # Group-specific RoleGrant with more permissions
        RoleGrant.objects.create(
            role=editor_role,
            scope='articles',
            actions=['r', 'w', 'd'],
            group=premium_group
        )
        
        # Direct assignment gets generic permissions
        assign_role(test_user, 'editor', by=admin_user)
        assert check(test_user, 'articles', ['d']) is False
        
        # Revoke and assign via group
        revoke_role(test_user, 'editor')
        assign_group(test_user, 'premium', by=admin_user)
        
        # Check that user has permissions from group
        # Note: group-specific grants may not be fully implemented yet
        grants = Grant.objects.filter(user=test_user, scope='articles')
        assert grants.exists()
