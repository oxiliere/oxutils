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
