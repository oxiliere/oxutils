from typing import Any
import uuid
from django.apps import apps
from django.conf import settings
from .constants import OXI_SYSTEM_TENANT




def get_model(setting: str) -> Any:
    try:
        value = getattr(settings, setting)
    except AttributeError:
        raise ValueError(f"Model `{setting}` is not a valid Tenant model.")

    return apps.get_model(value)


def get_tenant_model() -> Any:
    return get_model('TENANT_MODEL')

def get_tenant_user_model() -> Any:
    return get_model('TENANT_USER_MODEL')

def is_system_tenant(tenant: Any) -> bool:
    return tenant.oxi_id == get_system_tenant_oxi_id()

def get_system_tenant_oxi_id():
    return getattr(settings, 'OXI_SYSTEM_TENANT', OXI_SYSTEM_TENANT)

def oxid_to_schema_name(oxid: str) -> str:
    """
    Convertit un OXI-ID (slug) en nom de schéma PostgreSQL valide.
    
    Règles PostgreSQL pour les noms de schéma:
    - Doit commencer par une lettre (a-z) ou underscore (_)
    - Peut contenir uniquement des lettres, chiffres et underscores
    - Maximum 63 caractères
    - Sensible à la casse mais conventionnellement en minuscules
    
    Args:
        oxid: Slug de l'organisation (ex: "my-company", "acme-corp")
    
    Returns:
        Nom de schéma valide (format: tenant_mycompany, tenant_acmecorp)
    """
    if not oxid:
        raise ValueError("oxi_id cannot be empty")
    
    # Nettoyer le slug: remplacer les tirets par underscores et convertir en minuscules
    clean_id = str(oxid).replace('-', '_').lower()
    
    # Supprimer tous les caractères non-alphanumériques sauf underscore
    import re
    clean_id = re.sub(r'[^a-z0-9_]', '', clean_id)
    
    # Préfixer avec 'tenant_' pour s'assurer que ça commence par une lettre
    # et pour éviter les conflits avec les schémas système de PostgreSQL
    schema_name = f"tenant_{clean_id}"
    
    # Vérifier la longueur (PostgreSQL limite à 63 caractères)
    if len(schema_name) > 63:
        raise ValueError(f"Schema name too long: {len(schema_name)} characters (max 63)")
    
    return schema_name


def generate_schema_name(oxi_id: str, suffix: str = None) -> str:
    cleaned = oxid_to_schema_name(oxi_id)
    if suffix:
        return f"{cleaned}_{suffix}"
    return f"{cleaned}_{uuid.uuid4().hex[:8]}"


def update_tenant_user(oxi_org_id: str, oxi_user_id: str, data: dict):
    if not data or isinstance(data, dict) == False: return
    if not oxi_org_id or not oxi_user_id: return

    from oxutils.oxiliere.caches import get_tenant_user

    TENANT_USER_FIELDS = ['is_owner', 'is_admin', 'status', 'is_active']
    tenant_user = get_tenant_user(oxi_org_id, oxi_user_id)
    changes = False

    for key, value in data.items():
        if key in TENANT_USER_FIELDS:
            setattr(tenant_user, key, value)
            changes = True

    if changes:
        tenant_user.save()


def update_tenant(oxi_id: str, data: dict):
    if not data or isinstance(data, dict) == False: return
    if not oxi_id: return

    from oxutils.oxiliere.caches import get_tenant_by_oxi_id

    TENANT_FIELDS = ['name', 'status', 'subscription_plan', 'subscription_status', 'subscription_end_date']

    tenant = get_tenant_by_oxi_id(oxi_id)
    changes = False

    for key, value in data.items():
        if key in TENANT_FIELDS:
            setattr(tenant, key, value)
            changes = True

    if changes:
        tenant.save()
