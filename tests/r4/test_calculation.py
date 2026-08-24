from dataclasses import dataclass

from pourbaix_r4.calculation import calculate_snapshot
from pourbaix_r4.domain import parse_calculation_input


@dataclass(frozen=True)
class StubEntry:
    label: str = "PourbaixEntry(debug)"

    @property
    def name(self):
        return "Sb2Se3(s)"

    def __str__(self):
        return self.label


class StubDiagram:
    def __init__(self, entries, comp_dict):
        self.entries = entries
        self.comp_dict = comp_dict
        self.stable_entries = [StubEntry()]


class StubPlotter:
    def __init__(self, diagram):
        self.diagram = diagram

    def domain_vertices(self, entry):
        assert entry.name == "Sb2Se3(s)"
        return [(-2.0, -3.0), (16.0, -3.0), (16.0, 5.0), (-2.0, 5.0)]


def test_calculate_snapshot_clips_domain_vertices_and_keeps_open_species_out_of_composition():
    calculation_input = parse_calculation_input(
        ("Sb", "Se", "O"), {"Sb": "2", "Se": "3"}, (0, 14), (-2, 4),
        ion_concentrations={"Sb": "1e-6", "Se": "0.01"}, filter_solids=False,
    )
    received = {}

    def diagram_factory(entries, **kwargs):
        received["entries"] = entries
        received.update(kwargs)
        return StubDiagram(entries, kwargs["comp_dict"])

    snapshot = calculate_snapshot(
        calculation_input,
        entries=["source-entry"],
        diagram_factory=diagram_factory,
        plotter_factory=StubPlotter,
    )

    assert received == {
        "entries": ["source-entry"], "comp_dict": {"Sb": 2.0, "Se": 3.0},
        "conc_dict": {"Sb": 1e-6, "Se": 0.01}, "filter_solids": False,
    }
    assert snapshot.stable_domain_labels == ("Sb2Se3(s)",)
    assert snapshot.entries_count == 1
    assert snapshot.boundaries
    assert all(0.0 <= boundary.ph <= 14.0 for boundary in snapshot.boundaries)
    assert all(-2.0 <= boundary.potential_v_she <= 4.0 for boundary in snapshot.boundaries)
