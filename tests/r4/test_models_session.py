from dataclasses import FrozenInstanceError

import pytest

from pourbaix_r4.session import CalculationSession
from pourbaix_r4.models import (
    AppearanceSettings,
    BoundaryRecord,
    CalculationInput,
    InterestRegion,
    ResultSnapshot,
)


def test_calculation_input_is_immutable_and_exposes_closed_composition_only():
    calculation_input = CalculationInput(
        elements=("Ti", "O"),
        closed_element_ratios=(("Ti", 1.0),),
        ph_range=(0.0, 14.0),
        potential_range=(-2.0, 4.0),
    )

    assert calculation_input.comp_dict == {"Ti": 1.0}
    with pytest.raises(FrozenInstanceError):
        calculation_input.elements = ("Sb",)  # type: ignore[misc]


def test_snapshot_uses_immutable_records_without_qt_objects():
    calculation_input = CalculationInput(
        elements=("Fe", "Ni"),
        closed_element_ratios=(("Fe", 1.0), ("Ni", 1.0)),
        ph_range=(0.0, 14.0),
        potential_range=(-2.0, 4.0),
    )
    boundary = BoundaryRecord(domain_label="Fe(s)", ph=7.0, potential_v_she=-0.2)
    snapshot = ResultSnapshot(
        calculation_input=calculation_input,
        stable_domain_labels=("Fe(s)",),
        boundaries=(boundary,),
        entries_count=2,
    )

    assert snapshot.boundaries == (boundary,)
    assert InterestRegion(label="Fe(s)").visible is True
    assert AppearanceSettings().show_ion_labels is True


def test_session_blocks_export_for_stale_and_failed_calculations():
    calculation_input = CalculationInput(
        elements=("Ti",),
        closed_element_ratios=(("Ti", 1.0),),
        ph_range=(0.0, 14.0),
        potential_range=(-2.0, 4.0),
    )
    snapshot = ResultSnapshot(
        calculation_input=calculation_input,
        stable_domain_labels=("Ti(s)",),
        boundaries=(BoundaryRecord("Ti(s)", 7.0, -0.2),),
        entries_count=1,
    )
    session = CalculationSession()

    session.replace_success(snapshot)
    assert session.exportable_snapshot is snapshot

    session.invalidate_for_input_change()
    assert session.snapshot is snapshot
    assert session.exportable_snapshot is None

    session.replace_failure(RuntimeError("network unavailable"))
    assert session.snapshot is None
    assert session.exportable_snapshot is None
