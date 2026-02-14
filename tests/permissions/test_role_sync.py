"""
Tests for role_sync functionality.
"""
import pytest
from django.contrib.auth import get_user_model

from oxutils.permissions.models import Role, RoleGrant, Grant
from oxutils.permissions.utils import (
    assign_role,
    role_sync,
)
from oxutils.permissions.exceptions import RoleNotFoundException


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
def test_user2(db_setup):
    """Create a second test user."""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
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
def editor_role_grant(db_setup, editor_role):
    """Create a role grant for editor on articles."""
    return RoleGrant.objects.create(
        role=editor_role,
        scope='articles',
        actions=['r', 'w'],
        context={}
    )


class TestRoleSync:
    """Test role_sync functionality."""

    def test_role_sync_updates_independent_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test role_sync updates independent role grants after RoleGrant changes."""
        # Assign role independently (not via group)
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        
        # Verify initial grant
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group__isnull=True)
        assert set(grant.actions) == {'r', 'w'}
        
        # Modify role grant
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync role
        stats = role_sync('editor')
        
        assert stats['grants_updated'] == 1
        
        # Check grant was updated
        grant.refresh_from_db()
        assert 'd' in grant.actions

    def test_role_sync_with_scope_filter(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test role_sync with scope parameter for performance optimization."""
        # Create another role grant for different scope
        comments_grant = RoleGrant.objects.create(
            role=editor_role,
            scope='comments',
            actions=['r'],
            context={}
        )
        
        # Assign role independently
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assign_role(test_user, 'editor', 'comments', by=admin_user)
        
        # Modify editor role grant for articles
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync only articles scope
        stats = role_sync('editor', scope='articles')
        
        assert stats['grants_updated'] == 1
        
        # Check articles grant was updated
        articles_grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group__isnull=True)
        assert 'd' in articles_grant.actions
        
        # Check comments grant was NOT updated
        comments_grant_obj = Grant.objects.get(user=test_user, scope='comments', role=editor_role, user_group__isnull=True)
        assert set(comments_grant_obj.actions) == {'r'}

    def test_role_sync_multiple_users(self, test_user, test_user2, editor_role, editor_role_grant, admin_user):
        """Test role_sync updates grants for all users with independent role assignments."""
        # Assign role to multiple users independently
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        assign_role(test_user2, 'editor', 'articles', by=admin_user)
        
        # Modify role grant
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync role
        stats = role_sync('editor')
        
        assert stats['grants_updated'] == 2
        
        # Check both grants were updated
        grant1 = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group__isnull=True)
        grant2 = Grant.objects.get(user=test_user2, scope='articles', role=editor_role, user_group__isnull=True)
        assert 'd' in grant1.actions
        assert 'd' in grant2.actions

    def test_role_sync_preserves_locked_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test role_sync does not update locked (custom) grants."""
        # Assign role independently
        assign_role(test_user, 'editor', 'articles', by=admin_user)
        
        # Lock the grant (simulate override_grant)
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group__isnull=True)
        grant.locked = True
        grant.actions = ['r']  # Custom actions
        grant.save()
        
        # Modify role grant
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync role
        stats = role_sync('editor')
        
        assert stats['grants_updated'] == 0  # Locked grant not updated
        
        # Check grant was NOT updated
        grant.refresh_from_db()
        assert set(grant.actions) == {'r'}
        assert 'd' not in grant.actions

    def test_role_sync_ignores_group_grants(self, test_user, editor_role, editor_role_grant, admin_user):
        """Test role_sync only updates independent grants, not group-based grants."""
        # Create a grant with user_group (simulating group assignment)
        from oxutils.permissions.models import Group, UserGroup
        
        group = Group.objects.create(slug='staff', name='Staff')
        group.roles.add(editor_role)
        user_group = UserGroup.objects.create(user=test_user, group=group)
        
        Grant.objects.create(
            user=test_user,
            scope='articles',
            role=editor_role,
            actions=['r', 'w'],
            user_group=user_group,
            locked=False
        )
        
        # Modify role grant
        editor_role_grant.actions = ['r', 'w', 'd']
        editor_role_grant.save()
        
        # Sync role
        stats = role_sync('editor')
        
        assert stats['grants_updated'] == 0  # Group grant not updated by role_sync
        
        # Check grant was NOT updated
        grant = Grant.objects.get(user=test_user, scope='articles', role=editor_role, user_group=user_group)
        assert 'd' not in grant.actions

    def test_role_sync_role_not_found(self, db_setup):
        """Test role_sync raises exception for non-existent role."""
        with pytest.raises(RoleNotFoundException):
            role_sync('nonexistent')

    def test_role_sync_no_grants(self, editor_role, editor_role_grant):
        """Test role_sync with no grants to update."""
        # No users have this role independently
        stats = role_sync('editor')
        
        assert stats['grants_updated'] == 0
