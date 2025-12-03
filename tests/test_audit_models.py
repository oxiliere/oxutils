"""
Tests for audit models and migrations.
"""
import pytest
from oxutils.audit.models import LogExportState, LogExportHistory
from oxutils.enums.audit import ExportStatus


@pytest.mark.django_db
class TestLogExportState:
    """Test LogExportState model."""

    def test_create_export_state(self):
        """Test creating a new export state."""
        export_state = LogExportState.create(size=1024)
        
        assert export_state.id is not None
        assert export_state.status == ExportStatus.PENDING
        assert export_state.size == 1024
        assert export_state.last_export_date is None

    def test_set_success(self):
        """Test setting export state to success."""
        export_state = LogExportState.create(size=2048)
        export_state.set_success()
        
        export_state.refresh_from_db()
        assert export_state.status == ExportStatus.SUCCESS
        assert export_state.last_export_date is not None
        
        # Check history was created
        history = export_state.log_histories.first()
        assert history is not None
        assert history.status == ExportStatus.SUCCESS

    def test_set_failed(self):
        """Test setting export state to failed."""
        export_state = LogExportState.create(size=512)
        export_state.set_failed()
        
        export_state.refresh_from_db()
        assert export_state.status == ExportStatus.FAILED
        
        # Check history was created
        history = export_state.log_histories.first()
        assert history is not None
        assert history.status == ExportStatus.FAILED

    def test_timestamps(self):
        """Test that timestamps are automatically set."""
        export_state = LogExportState.create(size=256)
        
        assert export_state.created_at is not None
        assert export_state.updated_at is not None
        # Timestamps should be very close (within 1 second)
        time_diff = abs((export_state.updated_at - export_state.created_at).total_seconds())
        assert time_diff < 1.0


@pytest.mark.django_db
class TestLogExportHistory:
    """Test LogExportHistory model."""

    def test_create_history(self):
        """Test creating a history entry."""
        export_state = LogExportState.create(size=128)
        
        history = LogExportHistory.objects.create(
            state=export_state,
            status=ExportStatus.PENDING
        )
        
        assert history.id is not None
        assert history.state == export_state
        assert history.status == ExportStatus.PENDING
        assert history.created_at is not None

    def test_multiple_histories(self):
        """Test creating multiple history entries for one state."""
        export_state = LogExportState.create(size=64)
        
        # Create multiple history entries
        LogExportHistory.objects.create(
            state=export_state,
            status=ExportStatus.PENDING
        )
        LogExportHistory.objects.create(
            state=export_state,
            status=ExportStatus.SUCCESS
        )
        
        histories = export_state.log_histories.all()
        assert histories.count() == 2

    def test_cascade_delete(self):
        """Test that histories are deleted when state is deleted."""
        export_state = LogExportState.create(size=32)
        
        LogExportHistory.objects.create(
            state=export_state,
            status=ExportStatus.PENDING
        )
        
        state_id = export_state.id
        export_state.delete()
        
        # Check that history was also deleted
        histories = LogExportHistory.objects.filter(state_id=state_id)
        assert histories.count() == 0


@pytest.mark.django_db
class TestMigrations:
    """Test that migrations are properly applied."""

    def test_models_exist(self):
        """Test that models are accessible."""
        assert LogExportState is not None
        assert LogExportHistory is not None

    def test_can_create_instances(self):
        """Test that we can create model instances."""
        export_state = LogExportState.create(size=100)
        assert export_state.pk is not None
        
        history = LogExportHistory.objects.create(
            state=export_state,
            status=ExportStatus.PENDING
        )
        assert history.pk is not None
