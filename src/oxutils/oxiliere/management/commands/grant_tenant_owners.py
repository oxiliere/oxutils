from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.management.commands import InteractiveTenantOption
from oxutils.oxiliere.authorization import grant_manager_access_to_owners


class Command(InteractiveTenantOption, BaseCommand):
    help = "Wrapper around django commands for use with an individual tenant"

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def handle(self, *args, **options):
        tenant = self.get_tenant_from_options_or_interactive(**options)
        connection.set_tenant(tenant)
        options.pop('schema_name', None)

        grant_manager_access_to_owners(tenant)
        self.stdout.write(self.style.SUCCESS('Successfully granted manager access to owners'))
