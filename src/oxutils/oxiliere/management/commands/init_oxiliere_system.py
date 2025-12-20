import uuid
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model
from oxutils.oxiliere.models import Domain, TenantUser
from oxutils.oxiliere.utils import oxid_to_schema_name



class Command(BaseCommand):
    help = 'Initialise le tenant système Oxiliere'

    @transaction.atomic
    def handle(self, *args, **options):
        TenantModel = get_tenant_model()
        UserModel = get_user_model()
        
        # Configuration du tenant système depuis settings
        system_slug = getattr(settings, 'OXI_SYSTEM_TENANT', 'tenant_oxisystem')
        schema_name = oxid_to_schema_name(system_slug)
        system_domain = getattr(settings, 'OXI_SYSTEM_DOMAIN', 'system.oxiliere.com')
        owner_email = getattr(settings, 'OXI_SYSTEM_OWNER_EMAIL', 'dev@oxiliere.com')
        owner_oxi_id = uuid.uuid4()
        
        self.stdout.write(self.style.WARNING(f'Initialisation du tenant système...'))
        
        # Vérifier si le tenant système existe déjà
        if TenantModel.objects.filter(schema_name=schema_name).exists():
            self.stdout.write(self.style.ERROR(f'Le tenant système "{schema_name}" existe déjà!'))
            return
        
        # Créer le tenant système
        self.stdout.write(f'Création du tenant système: {schema_name}')
        tenant = TenantModel.objects.create(
            name='Oxiliere System',
            schema_name=schema_name,
            oxi_id=system_slug,
            subscription_plan='system',
            subscription_status='active',
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Tenant système créé: {tenant.name} ({tenant.schema_name})'))
        
        # Créer le domaine pour le tenant système
        self.stdout.write(f'Création du domaine: {system_domain}')
        domain = Domain.objects.create(
            domain=system_domain,
            tenant=tenant,
            is_primary=True
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Domaine créé: {domain.domain}'))
        
        self.stdout.write(f'Création du superuser: {owner_email}')
        try:
            superuser = UserModel.objects.get(email=owner_email)
            self.stdout.write(self.style.WARNING(f'⚠ Superuser existe déjà: {superuser.email}'))
        except UserModel.DoesNotExist:
            superuser = UserModel.objects.create_superuser(
                email=owner_email,
                oxi_id=owner_oxi_id,
                first_name='System',
                last_name='Admin'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Superuser créé: {superuser.email}'))
        
        # Lier le superuser au tenant système
        self.stdout.write('Liaison du superuser au tenant système')
        tenant_user, created = TenantUser.objects.get_or_create(
            tenant=tenant,
            user=superuser,
            defaults={
                'is_owner': True,
                'is_admin': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Superuser lié au tenant système'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Liaison existe déjà'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Initialisation terminée avec succès ==='))
        self.stdout.write(f'Tenant: {tenant.name}')
        self.stdout.write(f'Schema: {tenant.schema_name}')
        self.stdout.write(f'Domain: {domain.domain}')
        self.stdout.write(f'Superuser: {owner_email}')
