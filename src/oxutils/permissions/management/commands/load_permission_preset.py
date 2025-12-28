from typing import Any
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from oxutils.permissions.utils import load_preset


class Command(BaseCommand):
    """
    Commande de management Django pour charger un preset de permissions.
    
    Usage:
        python manage.py load_permission_preset
        python manage.py load_permission_preset --dry-run
        python manage.py load_permission_preset --force
        python manage.py load_permission_preset --dry-run --force
    """
    
    help = "Charge un preset de permissions depuis settings.PERMISSION_PRESET"

    def add_arguments(self, parser) -> None:
        """
        Ajoute les arguments de la commande.
        
        Args:
            parser: ArgumentParser de Django
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule le chargement sans créer les objets en base de données',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le chargement même si des rôles existent déjà en base',
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Exécute la commande de chargement du preset.
        
        Args:
            *args: Arguments positionnels
            **options: Options de la commande
            
        Raises:
            CommandError: Si le preset n'est pas défini ou est invalide
        """
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - Aucune modification ne sera effectuée')
            )
        
        if force:
            self.stdout.write(
                self.style.WARNING('Mode FORCE activé - Les rôles existants seront ignorés')
            )
        
        try:
            # Charger le preset
            self.stdout.write('Chargement du preset de permissions...')
            
            if dry_run:
                # En mode dry-run, on utilise un savepoint pour rollback
                sid = transaction.savepoint()
            
            stats = load_preset(force=force)
            
            if dry_run:
                # Rollback en mode dry-run
                transaction.savepoint_rollback(sid)
            
            # Afficher les statistiques
            self.stdout.write(
                self.style.SUCCESS('\n✓ Preset chargé avec succès!')
            )
            self.stdout.write(f"  • Rôles créés: {stats['roles']}")
            self.stdout.write(f"  • Groupes créés: {stats['groups']}")
            self.stdout.write(f"  • Role grants créés: {stats['role_grants']}")
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\nAucune modification effectuée (mode dry-run)')
                )
            
        except AttributeError as e:
            raise CommandError(
                f"Erreur de configuration: {str(e)}\n"
                "Assurez-vous que PERMISSION_PRESET est défini dans vos settings Django."
            )
        
        except PermissionError as e:
            raise CommandError(
                f"{str(e)}\n"
                "Utilisez --force pour forcer le chargement malgré les rôles existants."
            )
        
        except (KeyError, ValueError) as e:
            raise CommandError(
                f"Erreur dans le preset: {str(e)}\n"
                "Vérifiez la structure de votre PERMISSION_PRESET."
            )
        
        except Exception as e:
            raise CommandError(
                f"Erreur inattendue lors du chargement du preset: {str(e)}"
            )
