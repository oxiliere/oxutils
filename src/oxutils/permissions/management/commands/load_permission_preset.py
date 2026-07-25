from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from oxutils.permissions.utils import load_preset


class Command(BaseCommand):
    """
    Synchronise the database with ``settings.PERMISSION_PRESET``.

    The command is **idempotent** — running it multiple times is safe:
    new items are created, existing items are diffed and updated when
    their configuration changed, nothing is ever deleted.

    Usage::

        python manage.py load_permission_preset
        python manage.py load_permission_preset --dry-run
    """

    help = "Synchronise permissions from settings.PERMISSION_PRESET into the database"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate without writing to the database",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY-RUN mode — no changes will be persisted"
                )
            )

        try:
            self.stdout.write("Synchronising permission preset …")

            sid = None
            if dry_run:
                sid = transaction.savepoint()

            stats = load_preset()

            if dry_run and sid is not None:
                transaction.savepoint_rollback(sid)

            self.stdout.write(
                self.style.SUCCESS("\n✓ Preset synchronised successfully!")
            )

            for entity in ("roles", "groups", "role_grants"):
                created = stats[entity]["created"]
                updated = stats[entity]["updated"]
                if created or updated:
                    self.stdout.write(
                        f"  • {entity}: {created} created, {updated} updated"
                    )
                else:
                    self.stdout.write(f"  • {entity}: no changes")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "\nNo changes persisted (dry-run)"
                    )
                )

        except AttributeError as e:
            raise CommandError(
                f"Configuration error: {e}\n"
                "Make sure PERMISSION_PRESET is defined in your Django settings."
            ) from e

        except (KeyError, ValueError) as e:
            raise CommandError(
                f"Invalid preset: {e}\n"
                "Check the structure of your PERMISSION_PRESET."
            ) from e

        except Exception as e:
            raise CommandError(
                f"Unexpected error while loading the preset: {e}"
            ) from e
