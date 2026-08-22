from pathlib import Path

import pandas as pd
import pytest

from pourbaix_r4.exporting import ExportError, export_boundaries
from pourbaix_r4.models import BoundaryRecord, CalculationInput, ResultSnapshot


def _snapshot():
    return ResultSnapshot(
        calculation_input=CalculationInput(
            elements=("Fe", "Ni"),
            closed_element_ratios=(("Fe", 1.0), ("Ni", 1.0)),
            ph_range=(0.0, 14.0),
            potential_range=(-2.0, 4.0),
        ),
        stable_domain_labels=("Fe(s)",),
        boundaries=(
            BoundaryRecord("Fe(s)", 0.0, -2.0),
            BoundaryRecord("Fe(s)", 14.0, 4.0),
        ),
        entries_count=2,
    )


@pytest.mark.parametrize("file_format", ["csv", "xlsx", "txt"])
def test_export_boundaries_writes_fixed_english_headers_and_readable_data(tmp_path, file_format):
    path = tmp_path / f"boundaries.{file_format}"

    written = export_boundaries(_snapshot(), path, file_format)

    assert written == path
    assert path.stat().st_size > 0
    if file_format == "xlsx":
        data = pd.read_excel(path)
    else:
        data = pd.read_csv(path, sep="\t" if file_format == "txt" else ",")
    assert list(data.columns) == ["domain_label", "vertex_index", "pH", "potential_V_SHE"]
    assert data["domain_label"].tolist() == ["Fe(s)", "Fe(s)"]


def test_export_boundaries_rejects_unknown_format_without_refetching(tmp_path):
    with pytest.raises(ExportError, match="Unsupported"):
        export_boundaries(_snapshot(), tmp_path / "boundaries.json", "json")
