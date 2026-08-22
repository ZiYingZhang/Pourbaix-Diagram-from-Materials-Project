from dataclasses import dataclass

import pytest

from pourbaix_r4.credentials import (
    CredentialError,
    api_docs_url,
    api_key_url,
    detect_legacy_key,
    forget_saved_key,
    migrate_legacy_key,
    remember_api_key,
    resolve_api_key,
)


@dataclass
class FakeCredentialStore:
    value: str | None = None
    fail_on_write: bool = False

    def get(self) -> str | None:
        return self.value

    def set(self, api_key: str) -> None:
        if self.fail_on_write:
            raise CredentialError("secure storage unavailable")
        self.value = api_key

    def delete(self) -> None:
        self.value = None


def test_resolve_api_key_prefers_current_value_without_exposing_it(tmp_path):
    resolved = resolve_api_key(
        current_value="current-secret",
        store=FakeCredentialStore("stored-secret"),
        legacy_path=tmp_path / "mp_api_key.txt",
        environ={"MP_API_KEY": "environment-secret"},
    )

    assert resolved.value == "current-secret"
    assert resolved.source == "current_ui"
    assert "current-secret" not in repr(resolved)


@pytest.mark.parametrize(
    ("environ", "expected_source", "expected_value"),
    [
        ({"MP_API_KEY": "mp-secret", "MAPI_KEY": "mapi-secret"}, "environment:MP_API_KEY", "mp-secret"),
        ({"MAPI_KEY": "mapi-secret", "PMG_MAPI_KEY": "pmg-secret"}, "environment:MAPI_KEY", "mapi-secret"),
        ({"PMG_MAPI_KEY": "pmg-secret"}, "environment:PMG_MAPI_KEY", "pmg-secret"),
    ],
)
def test_resolve_api_key_uses_documented_environment_order(tmp_path, environ, expected_source, expected_value):
    resolved = resolve_api_key(None, FakeCredentialStore(), tmp_path / "mp_api_key.txt", environ)

    assert resolved.source == expected_source
    assert resolved.value == expected_value


def test_resolve_api_key_prefers_secure_store_before_environment_and_legacy(tmp_path):
    legacy_path = tmp_path / "mp_api_key.txt"
    legacy_path.write_text("legacy-secret\n", encoding="utf-8")

    resolved = resolve_api_key(
        current_value=" ",
        store=FakeCredentialStore("stored-secret"),
        legacy_path=legacy_path,
        environ={"MP_API_KEY": "environment-secret"},
    )

    assert resolved.source == "windows_credential_manager"
    assert resolved.value == "stored-secret"
    assert legacy_path.read_text(encoding="utf-8") == "legacy-secret\n"


def test_legacy_key_is_read_compatibly_but_only_explicit_migration_writes_secure_storage(tmp_path):
    legacy_path = tmp_path / "mp_api_key.txt"
    legacy_path.write_text("legacy-secret\n", encoding="utf-8")
    store = FakeCredentialStore()

    assert detect_legacy_key(legacy_path) == "legacy-secret"
    resolved = resolve_api_key(None, store, legacy_path, environ={})
    assert resolved.source == "legacy_file"
    assert store.value is None

    migrated = migrate_legacy_key(store, legacy_path)
    assert migrated.source == "legacy_file"
    assert store.value == "legacy-secret"
    assert legacy_path.read_text(encoding="utf-8") == "legacy-secret\n"


def test_remember_replace_and_forget_are_delegated_to_secure_store():
    store = FakeCredentialStore()

    remember_api_key(store, "first-secret")
    remember_api_key(store, "replacement-secret")
    assert store.value == "replacement-secret"

    forget_saved_key(store)
    assert store.value is None


def test_secure_storage_failure_is_actionable_and_never_contains_the_key():
    with pytest.raises(CredentialError, match="secure storage unavailable") as error:
        remember_api_key(FakeCredentialStore(fail_on_write=True), "very-secret-value")

    assert "very-secret-value" not in str(error.value)


def test_materials_project_key_and_help_urls_are_maintained_separately():
    assert api_key_url() == "https://next-gen.materialsproject.org/api"
    assert api_docs_url() == "https://docs.materialsproject.org/downloading-data/using-the-api/getting-started"
