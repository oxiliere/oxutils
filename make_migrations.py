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
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'oxutils.audit',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    )
    django.setup()

if __name__ == '__main__':
    print("Generating migrations for oxutils.audit...")
    call_command('makemigrations', 'audit', '--verbosity', '2')
    print("\nMigrations created successfully!")
