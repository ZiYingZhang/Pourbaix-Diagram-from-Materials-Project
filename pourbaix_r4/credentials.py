"""Secret-safe Materials Project credential resolution for R4."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import keyring


_SERVICE_NAME = "PourbaixStudio.R4"
_ACCOUNT_NAME = "materials-project-api-key"
_ENVIRONMENT_VARIABLES = ("MP_API_KEY", "MAPI_KEY", "PMG_MAPI_KEY")
_API_KEY_URL = "https://next-gen.materialsproject.org/api"
_API_DOCS_URL = "https://docs.materialsproject.org/downloading-data/using-the-api/getting-started"


class CredentialError(RuntimeError):
    """A safe, user-actionable API credential failure."""


class CredentialStore(Protocol):
    def get(self) -> str | None: ...

    def set(self, api_key: str) -> None: ...

    def delete(self) -> None: ...


@dataclass(frozen=True)
class ResolvedCredential:
    source: str
    value: str = field(repr=False)


class WindowsCredentialStore:
    """Use the keyring Windows backend without writing plaintext files."""

    def get(self) -> str | None:
        try:
            return _nonempty(keyring.get_password(_SERVICE_NAME, _ACCOUNT_NAME))
        except Exception as error:
            raise CredentialError("Windows Credential Manager could not be accessed") from error

    def set(self, api_key: str) -> None:
        value = _require_key(api_key)
        try:
            keyring.set_password(_SERVICE_NAME, _ACCOUNT_NAME, value)
        except Exception as error:
            raise CredentialError("Windows Credential Manager could not save the API key") from error

    def delete(self) -> None:
        try:
            keyring.delete_password(_SERVICE_NAME, _ACCOUNT_NAME)
        except keyring.errors.PasswordDeleteError:
            return
        except Exception as error:
            raise CredentialError("Windows Credential Manager could not remove the API key") from error


def _nonempty(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _require_key(value: object) -> str:
    normalized = _nonempty(value)
    if not normalized:
        raise CredentialError("A Materials Project API key is required")
    return normalized


def api_key_url() -> str:
    """Return the R2.8 direct Materials Project API-key page."""
    return _API_KEY_URL


def api_docs_url() -> str:
    """Return the separately maintained official Materials Project API guide."""
    return _API_DOCS_URL


def detect_legacy_key(legacy_path: Path) -> str | None:
    """Read a legacy plaintext file without modifying it."""
    if not legacy_path.is_file():
        return None
    try:
        return _nonempty(legacy_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CredentialError("The legacy API-key file could not be read") from error


def resolve_api_key(
    current_value: str | None,
    store: CredentialStore,
    legacy_path: Path,
    environ: Mapping[str, str] | None = None,
) -> ResolvedCredential:
    """Resolve one key using the documented, secret-safe precedence order."""
    current = _nonempty(current_value)
    if current:
        return ResolvedCredential(source="current_ui", value=current)

    remembered = _nonempty(store.get())
    if remembered:
        return ResolvedCredential(source="windows_credential_manager", value=remembered)

    environment = os.environ if environ is None else environ
    for variable in _ENVIRONMENT_VARIABLES:
        value = _nonempty(environment.get(variable))
        if value:
            return ResolvedCredential(source=f"environment:{variable}", value=value)

    legacy = detect_legacy_key(legacy_path)
    if legacy:
        return ResolvedCredential(source="legacy_file", value=legacy)
    raise CredentialError("A Materials Project API key is required before querying")


def remember_api_key(store: CredentialStore, api_key: str) -> None:
    """Persist a supplied key only through the injected secure store."""
    store.set(_require_key(api_key))


def forget_saved_key(store: CredentialStore) -> None:
    """Remove the R4 credential record from the secure store."""
    store.delete()


def migrate_legacy_key(store: CredentialStore, legacy_path: Path) -> ResolvedCredential:
    """Explicitly copy a legacy key into secure storage without deleting it."""
    legacy = detect_legacy_key(legacy_path)
    if not legacy:
        raise CredentialError("No legacy Materials Project API key was found")
    remember_api_key(store, legacy)
    return ResolvedCredential(source="legacy_file", value=legacy)
