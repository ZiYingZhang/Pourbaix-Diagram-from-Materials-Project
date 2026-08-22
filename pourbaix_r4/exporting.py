"""Snapshot-based scientific data and figure export helpers."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Literal

import pandas as pd

from pourbaix_r4.models import ResultSnapshot


class ExportError(RuntimeError):
    """A safe, actionable failure while writing an already-calculated result."""


_DATA_COLUMNS = ["domain_label", "vertex_index", "pH", "potential_V_SHE"]


def _boundary_frame(snapshot: ResultSnapshot) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "domain_label": boundary.domain_label,
                "vertex_index": boundary.vertex_index,
                "pH": boundary.ph,
                "potential_V_SHE": boundary.potential_v_she,
            }
            for boundary in snapshot.boundaries
        ],
        columns=_DATA_COLUMNS,
    )


def _verified_atomic_write(path: Path, writer) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=path.suffix, dir=path.parent)
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        writer(temporary_path)
        if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
            raise ExportError("Export did not create a non-empty file")
        os.replace(temporary_path, path)
        return path
    except ExportError:
        raise
    except Exception as error:
        raise ExportError("Could not write the requested boundary export") from error
    finally:
        temporary_path.unlink(missing_ok=True)


def export_boundaries(
    snapshot: ResultSnapshot,
    path: Path,
    file_format: Literal["csv", "xlsx", "txt"],
) -> Path:
    """Export one immutable snapshot without recalculating or refetching entries."""
    if file_format not in {"csv", "xlsx", "txt"}:
        raise ExportError(f"Unsupported boundary export format: {file_format}")
    frame = _boundary_frame(snapshot)

    def write(temporary_path: Path) -> None:
        if file_format == "csv":
            frame.to_csv(temporary_path, index=False)
        elif file_format == "txt":
            frame.to_csv(temporary_path, index=False, sep="\t")
        else:
            metadata = pd.DataFrame(
                {
                    "field": ["entries_count", "pH_range", "potential_range"],
                    "value": [
                        snapshot.entries_count,
                        str(snapshot.calculation_input.ph_range),
                        str(snapshot.calculation_input.potential_range),
                    ],
                }
            )
            with pd.ExcelWriter(temporary_path) as writer:
                frame.to_excel(writer, sheet_name="boundaries", index=False)
                metadata.to_excel(writer, sheet_name="metadata", index=False)

    return _verified_atomic_write(Path(path), write)
