import pytest

from pourbaix_core import fetch_pourbaix_entries


VALID_ION_RECORD = {
    "identifier": "Ti[+2]",
    "data": {"MajElements": "Ti", "RefSolid": "TiO2", "optional": None},
}
MALFORMED_ION_RECORD = {"identifier": "bad", "data": {"MajElements": "Ti"}}


class ControlledMPRester:
    def __init__(self, outcomes, ion_records=None):
        self.outcomes = list(outcomes)
        self.ion_records = list(ion_records or [])
        self.pourbaix_calls = 0
        self.ion_calls = 0
        self.selected_ion_records = None

    def get_pourbaix_entries(self, _elements):
        self.pourbaix_calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if self.pourbaix_calls == 2:
            self.selected_ion_records = self.get_ion_reference_data_for_chemsys(["Ti"])
        return outcome

    def get_ion_reference_data(self):
        self.ion_calls += 1
        return self.ion_records

    def get_ion_reference_data_for_chemsys(self, chemsys):
        return [record for record in self.ion_records if record["data"]["MajElements"] in chemsys]


def test_successful_initial_fetch_does_not_sanitize_or_retry():
    client = ControlledMPRester([["entry"]])

    result = fetch_pourbaix_entries(client, ["Ti"])

    assert result.entries == ["entry"]
    assert result.used_sanitation_retry is False
    assert client.pourbaix_calls == 1
    assert client.ion_calls == 0


def test_empty_initial_result_runs_one_sanitation_retry():
    client = ControlledMPRester(
        [[], ["recovered"]],
        [VALID_ION_RECORD, MALFORMED_ION_RECORD],
    )

    result = fetch_pourbaix_entries(client, ["Ti"])

    assert result.entries == ["recovered"]
    assert result.used_sanitation_retry is True
    assert client.pourbaix_calls == 2
    assert client.ion_calls == 1
    assert client.selected_ion_records == [
        {"identifier": "Ti[+2]", "data": {"MajElements": "Ti", "RefSolid": "TiO2"}}
    ]


@pytest.mark.parametrize("missing_field", ["data", "MajElements", "RefSolid"])
def test_missing_ion_field_exception_runs_one_sanitation_retry(missing_field):
    client = ControlledMPRester(
        [KeyError(missing_field), ["recovered"]],
        [VALID_ION_RECORD, MALFORMED_ION_RECORD],
    )

    result = fetch_pourbaix_entries(client, ["Ti"])

    assert result.entries == ["recovered"]
    assert result.used_sanitation_retry is True
    assert client.pourbaix_calls == 2
    assert client.ion_calls == 1


def test_unrelated_exception_is_preserved_without_retry():
    client = ControlledMPRester([RuntimeError("server unavailable")])

    with pytest.raises(RuntimeError, match="server unavailable"):
        fetch_pourbaix_entries(client, ["Ti"])

    assert client.pourbaix_calls == 1
    assert client.ion_calls == 0


def test_failed_retry_stops_after_exactly_two_total_attempts():
    client = ControlledMPRester(
        [KeyError("MajElements"), []],
        [VALID_ION_RECORD],
    )

    with pytest.raises(RuntimeError, match="No pourbaix entries after sanitation retry"):
        fetch_pourbaix_entries(client, ["Ti"])

    assert client.pourbaix_calls == 2
    assert client.ion_calls == 1


def test_gui_entry_fetch_uses_targeted_retry_and_updates_metrics(qapplication, monkeypatch):
    import mp_api.client
    from pourbaix_gui_R3 import PourbaixApp

    controlled = ControlledMPRester(
        [KeyError("MajElements"), ["recovered"]],
        [VALID_ION_RECORD, MALFORMED_ION_RECORD],
    )

    class ContextMPRester:
        def __init__(self, api_key):
            assert api_key == "runtime-only-key"

        def __enter__(self):
            return controlled

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(mp_api.client, "MPRester", ContextMPRester)
    window = PourbaixApp()
    try:
        entries = window._safe_get_entries("runtime-only-key", ["Ti"])

        assert entries == ["recovered"]
        assert window._last_sanitation_retry is True
        assert window._last_entries_count == 1
        assert window._last_fetch_seconds >= 0
    finally:
        window.close()
