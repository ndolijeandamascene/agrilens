"""
Pytest configuration for AgriLens test suite.
"""
import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
