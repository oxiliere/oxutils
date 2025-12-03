"""
Pytest configuration for oxutils tests.
"""
import os
import sys
import pytest

# Add src to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))


def pytest_configure(config):
    """
    Set minimal S3 environment variables required for audit models to load.
    These must be set before Django apps are loaded.
    """
    os.environ.setdefault('OXI_SERVICE_NAME', 'test-service')
    os.environ.setdefault('OXI_USE_LOG_S3', 'True')
    os.environ.setdefault('OXI_USE_PRIVATE_S3', 'True')
    os.environ.setdefault('OXI_USE_PRIVATE_S3_AS_LOG', 'True')
    os.environ.setdefault('OXI_PRIVATE_S3_STORAGE_BUCKET_NAME', 'test-bucket')
    os.environ.setdefault('OXI_PRIVATE_S3_ACCESS_KEY_ID', 'test-key')
    os.environ.setdefault('OXI_PRIVATE_S3_SECRET_ACCESS_KEY', 'test-secret')
    os.environ.setdefault('OXI_PRIVATE_S3_S3_CUSTOM_DOMAIN', 'test.example.com')
