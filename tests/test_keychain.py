"""
Tests for keychain_helper.py - API key storage.
"""

import pytest


class TestKeychain:
    """Tests for keychain_helper.py - API key storage"""

    def test_service_name_defined(self):
        """Service name should be defined"""
        from keychain_helper import SERVICE_NAME, ACCOUNT_NAME

        assert SERVICE_NAME == "rephrase-app"
        assert ACCOUNT_NAME == "openai-api-key"

    def test_set_and_get_api_key(self, mock_keychain):
        """Should set and get API key via keyring"""
        from keychain_helper import get_api_key, set_api_key

        set_api_key("sk-test-12345")
        assert get_api_key() == "sk-test-12345"

    def test_get_api_key_returns_none_when_not_set(self, monkeypatch):
        """Should return None when no key is set"""
        from keychain_helper import get_api_key

        monkeypatch.setattr("keyring.get_password", lambda s, a: None)

        assert get_api_key() is None

    def test_delete_api_key_no_error_when_missing(self, monkeypatch):
        """delete_api_key should not raise when key doesn't exist"""
        from keychain_helper import delete_api_key
        import keyring

        def mock_delete(service, account):
            raise keyring.errors.PasswordDeleteError("Not found")

        monkeypatch.setattr("keyring.delete_password", mock_delete)

        # Should not raise
        delete_api_key()
