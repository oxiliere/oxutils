import os
from typing import Dict, Optional


def get_s3_storage_backend(storage_type: str, **kwargs) -> Optional[Dict]:
    """
    load env variables for storage_type

    OXI_<storage_type>_STORAGE_ACCESS_KEY_ID
    OXI_<storage_type>_STORAGE_SECRET_ACCESS_KEY
    OXI_<storage_type>_STORAGE_BUCKET_NAME
    OXI_<storage_type>_STORAGE_ENDPOINT_URL

    Args:
        storage_type: Type de storage (ex: "STATIC", "MEDIA")
        **kwargs: Options supplémentaires à ajouter ou surcharger dans OPTIONS

    return {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            ... options here if available
        }
    }
    """

    storage_type_upper = storage_type.upper()
    prefix = f"OXI_{storage_type_upper}_STORAGE_"

    # Vérifier si S3 est activé pour ce type de storage
    use_s3 = os.getenv(f"{prefix}USE_S3", "False").lower() in ("true", "1", "yes")

    if not use_s3:
        return None

    # Mapping des noms de variables d'environnement vers les options de storages
    env_to_option_mapping = {
        "ACCESS_KEY_ID": "access_key",
        "SECRET_ACCESS_KEY": "secret_key",
        "BUCKET_NAME": "bucket_name",
        "ENDPOINT_URL": "endpoint_url",
        "REGION_NAME": "region_name",
        "DEFAULT_ACL": "default_acl",
        "LOCATION": "location",
        "CUSTOM_DOMAIN": "custom_domain",
        "SIGNATURE_VERSION": "signature_version",
        "ADDRESSING_STYLE": "addressing_style",
        "USE_SSL": "use_ssl",
        "VERIFY": "verify",
        "QUERYSTRING_AUTH": "querystring_auth",
        "QUERYSTRING_EXPIRE": "querystring_expire",
        "FILE_OVERWRITE": "file_overwrite",
        "GZIP": "gzip",
        "URL_PROTOCOL": "url_protocol",
        "SECURITY_TOKEN": "security_token",
        "SESSION_PROFILE": "session_profile",
        "OBJECT_PARAMETERS": "object_parameters",
        "MAX_MEMORY_SIZE": "max_memory_size",
        "GZIP_CONTENT_TYPES": "gzip_content_types",
        "PROXIES": "proxies",
        "CLOUDFRONT_KEY": "cloudfront_key",
        "CLOUDFRONT_KEY_ID": "cloudfront_key_id",
        "CLOUDFRONT_SIGNER": "cloudfront_signer",
        "CLIENT_CONFIG": "client_config",
    }

    options = {}

    # Charger les variables d'environnement disponibles
    for env_suffix, option_name in env_to_option_mapping.items():
        env_var = f"{prefix}{env_suffix}"
        value = os.getenv(env_var)

        if value is not None:
            # Nettoyer les guillemets si présents
            value = value.strip("'\"")

            # Convertir les booléens
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            # Convertir les entiers
            elif value.isdigit():
                value = int(value)

            # Ajouter seulement si la valeur n'est pas vide
            if value != "":
                options[option_name] = value

    # Fusionner avec les kwargs fournis (les kwargs ont la priorité)
    options.update(kwargs)

    return {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": options}


def get_s3_static_url(options: Dict | None) -> Optional[str]:
    if options is None:
        return None

    custom_domain = options.get("OPTIONS", {}).get("custom_domain")
    location = options.get("OPTIONS", {}).get("location", "")
    protocol = options.get("OPTIONS", {}).get("url_protocol", "https")

    if custom_domain is None:
        return None

    url = f"{protocol}://{custom_domain}/"

    if location != "":
        url += location + "/"

    return url
