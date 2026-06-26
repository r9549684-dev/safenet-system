"""Pytest fixtures for SafeNet tests.

Provides mock settings to make tests portable (no .env dependency).
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock app.config.settings for all tests.
    
    This makes tests portable — no need for .env file.
    All tests use consistent mock values.
    """
    mock = MagicMock()
    mock.XRAY_PORT = 443
    mock.TROJAN_PORT = 443
    mock.AMNEZIA_PORT = 51820
    mock.XRAY_UUID = "550e8400-e29b-41d4-a716-446655440000"
    mock.XRAY_PUBLIC_KEY = "test_public_key_base64"
    mock.XRAY_SHORT_ID = "deadbeef"
    mock.TROJAN_PASSWORD = "test_password"
    mock.AMNEZIA_PRIVATE_KEY = "test_amnezia_private_key_base64"
    mock.AMNEZIA_PUBLIC_KEY = "test_amnezia_public_key_base64"
    mock.AMNEZIA_PRESHARED_KEY = "test_amnezia_preshared_key_base64"
    monkeypatch.setattr("app.config.settings", mock)
