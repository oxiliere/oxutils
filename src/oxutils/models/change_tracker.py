"""
Mixin that tracks field changes on Django models.

Usage::

    class MyModel(ChangeTrackerMixin, models.Model):
        TRACKED_FIELDS = ("status", "subscription_plan")

        def save(self, *args, **kwargs):
            changed = self.pop_changes()  # dict of {field: old_value}
            super().save(*args, **kwargs)
            if changed:
                do_something(changed)
"""
from typing import Dict, Optional, Tuple


class ChangeTrackerMixin:
    """
    Lightweight mixin that snapshots tracked fields before save and
    exposes a ``pop_changes()`` method to retrieve what changed.

    Subclasses set ``TRACKED_FIELDS`` to a tuple of field names.
    """

    TRACKED_FIELDS: Tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._snapshot: Dict[str, object] = {}

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._snapshot = cls._build_snapshot(instance)
        return instance

    def pop_changes(self) -> Dict[str, object]:
        """Return a dict of {field_name: old_value} for changed tracked fields
        and clear the snapshot so subsequent saves don't re-trigger."""
        changes = {}
        if not self.TRACKED_FIELDS:
            return changes

        for field in self.TRACKED_FIELDS:
            new_val = getattr(self, field)
            old_val = self._snapshot.get(field)
            if new_val != old_val:
                changes[field] = old_val

        self._snapshot = {}
        return changes

    @staticmethod
    def _build_snapshot(instance) -> Dict[str, object]:
        return {
            f: getattr(instance, f)
            for f in instance.TRACKED_FIELDS
            if hasattr(instance, f)
        }

    def refresh_snapshot(self) -> None:
        """Re-take the snapshot (useful after a save without changes)."""
        self._snapshot = self._build_snapshot(self)
