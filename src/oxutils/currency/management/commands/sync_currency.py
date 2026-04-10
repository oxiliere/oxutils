from django.core.management.base import BaseCommand

from oxutils.currency.models import CurrencyState


class Command(BaseCommand):
    help = "Synchronise les taux de change via CurrencyState.sync()"

    def handle(self, *args, **options):
        try:
            state = CurrencyState.sync()
            self.stdout.write(self.style.SUCCESS(f"Synchronisation réussie (state={state.id})"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Échec de la synchronisation : {e}"))
            raise SystemExit(1)
