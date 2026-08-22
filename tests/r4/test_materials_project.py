from dataclasses import dataclass

import pytest

from pourbaix_core import FetchResult
from pourbaix_r4.materials_project import CachedEntryService, MPResterEntryProvider


@dataclass
class RecordingProvider:
    result: FetchResult
    calls: list[tuple[tuple[str, ...], str]]

    def fetch(self, elements, api_key):
        self.calls.append((tuple(elements), api_key))
        return self.result


def test_cached_service_uses_canonical_chemical_system_without_storing_api_key():
    provider = RecordingProvider(FetchResult(entries=["entry"], used_sanitation_retry=False), [])
    service = CachedEntryService(provider, clock=lambda: 100.0)

    first = service.fetch(("ni", "Fe"), "first-secret")
    second = service.fetch(("Fe", "Ni"), "replacement-secret")
    diagnostics = service.diagnostics()

    assert first.entries == ["entry"]
    assert second.entries == ["entry"]
    assert provider.calls == [(("Fe", "Ni"), "first-secret")]
    assert diagnostics.cache_items == 1
    assert diagnostics.last_entries_count == 1
    assert "secret" not in repr(diagnostics)


def test_cached_service_refetches_after_five_minute_expiry():
    now = [100.0]
    provider = RecordingProvider(FetchResult(entries=["entry"], used_sanitation_retry=True), [])
    service = CachedEntryService(provider, clock=lambda: now[0])

    service.fetch(("Ti",), "runtime-secret")
    now[0] += 301.0
    service.fetch(("Ti",), "runtime-secret")

    assert len(provider.calls) == 2
    assert service.diagnostics().last_used_sanitation_retry is True


def test_clear_removes_cache_metadata_without_mutating_existing_entries():
    entries = ["entry"]
    provider = RecordingProvider(FetchResult(entries=entries, used_sanitation_retry=False), [])
    service = CachedEntryService(provider, clock=lambda: 100.0)
    result = service.fetch(("Ti",), "runtime-secret")

    service.clear()

    assert result.entries == ["entry"]
    assert service.diagnostics().cache_items == 0
    assert service.diagnostics().last_entries_count == 0


class ControlledMPRester:
    def __init__(self):
        self.contribs = object()
        self.calls = 0

    def get_pourbaix_entries(self, elements):
        self.calls += 1
        return [f"entry:{'-'.join(elements)}"]


class ContextFactory:
    def __init__(self, client):
        self.client = client
        self.received_key = None

    def __call__(self, api_key):
        self.received_key = api_key
        return self

    def __enter__(self):
        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_mprester_provider_delegates_to_proven_sanitation_fetch_helper():
    client = ControlledMPRester()
    factory = ContextFactory(client)
    provider = MPResterEntryProvider(mpr_factory=factory)

    result = provider.fetch(("Ti",), "runtime-secret")

    assert result.entries == ["entry:Ti"]
    assert result.used_sanitation_retry is False
    assert client.calls == 1
    assert factory.received_key == "runtime-secret"


def test_provider_preserves_unrelated_materials_project_errors():
    class FailingMPRester(ControlledMPRester):
        def get_pourbaix_entries(self, elements):
            raise RuntimeError("server unavailable")

    provider = MPResterEntryProvider(mpr_factory=ContextFactory(FailingMPRester()))

    with pytest.raises(RuntimeError, match="server unavailable"):
        provider.fetch(("Ti",), "runtime-secret")
