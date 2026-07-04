"""Secure API key storage in the OS credential store via keyring.

macOS: Keychain. Windows: Credential Manager (WinVault).
"""

import sys

import keyring

# In packaged apps (py2app/PyInstaller set sys.frozen), keyring's automatic
# backend discovery can fail because it scans package metadata that isn't
# shipped in the bundle - pin the native backend explicitly.
if getattr(sys, "frozen", None):
    if sys.platform == "darwin":
        from keyring.backends import macOS

        keyring.set_keyring(macOS.Keyring())
    elif sys.platform == "win32":
        from keyring.backends import Windows

        keyring.set_keyring(Windows.WinVaultKeyring())

SERVICE_NAME = "rephrase-app"
ACCOUNT_NAME = "openai-api-key"


def get_api_key() -> str | None:
    """Retrieve API key from Keychain."""
    return keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)


def set_api_key(api_key: str) -> None:
    """Store API key in Keychain."""
    keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, api_key)


def delete_api_key() -> None:
    """Remove API key from Keychain."""
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except keyring.errors.PasswordDeleteError:
        pass  # Key doesn't exist, that's fine
