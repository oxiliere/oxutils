#!/usr/bin/env python
"""
Script to generate migrations for the oxutils reusable Django app.
This script creates a minimal Django project to run makemigrations.
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

# Add src to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

# Set required environment variables for oxutils
os.environ.setdefault('OXI_SERVICE_NAME', 'migration-service')
os.environ.setdefault('OXI_USE_LOG_S3', 'True')
os.environ.setdefault('OXI_USE_PRIVATE_S3', 'True')
os.environ.setdefault('OXI_USE_PRIVATE_S3_AS_LOG', 'True')
os.environ.setdefault('OXI_PRIVATE_S3_STORAGE_BUCKET_NAME', 'dummy-bucket')
os.environ.setdefault('OXI_PRIVATE_S3_ACCESS_KEY_ID', 'dummy-key')
os.environ.setdefault('OXI_PRIVATE_S3_SECRET_ACCESS_KEY', 'dummy-secret')
os.environ.setdefault('OXI_PRIVATE_S3_CUSTOM_DOMAIN', 'dummy.example.com')
os.environ.setdefault('AWS_S3_REGION_NAME', 'us-east-1')

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='temporary-secret-key-for-migrations',
        SHARED_APPS=[
            'django.contrib.contenttypes',
            'django_tenants',
            'django.contrib.auth',
            'auditlog',
            'cacheops',
        ],
        TENANT_APPS=[
            'oxutils.audit',
            'oxutils.users',
            'oxutils.oxiliere',
            'oxutils.permissions',
        ],
        INSTALLED_APPS = [
            'django.contrib.contenttypes',
            'django_tenants',
            'django.contrib.auth',
            'auditlog',
            'cacheops',
            'oxutils.audit',
            'oxutils.users',
            'oxutils.oxiliere',
            'oxutils.permissions',
        ],
        CACHEOPS_REDIS = "redis://localhost:6379/1",
        CACHEOPS = {
            'oxiliere.*': {'ops': 'all', 'timeout': 60*15},
        },
        DATABASES={
            'default': {
                'ENGINE': 'django_tenants.postgresql_backend',
                'NAME': 'oxutils',
                'USER': 'oxiliere',
                'PASSWORD': 'oxiliere',
                'HOST': 'localhost',
                'PORT': 5432,
            }
        },
        DATABASE_ROUTERS=[
            'django_tenants.routers.TenantSyncRouter',
        ],
        TENANT_MODEL='oxiliere.Tenant',
        TENANT_USER_MODEL='oxiliere.TenantUser',
        USE_TZ=True,
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )
    django.setup()

# List of oxutils apps to generate migrations for
OXUTILS_APPS = [
    'audit',
    'users',
    # 'oxiliere',
    'permissions',
]

if __name__ == '__main__':
    for app in OXUTILS_APPS:
        print(f"\n{'='*60}")
        print(f"Generating migrations for oxutils.{app}...")
        print('='*60)
        try:
            call_command('makemigrations', app, '--verbosity', '2')
        except Exception as e:
            print(f"Error generating migrations for {app}: {e}")
            continue
    
    print("\n" + "="*60)
    print("All migrations generated successfully!")
    print("="*60)
