"""Build immutable R4 equilibrium snapshots from pymatgen results."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram, PourbaixPlotter
from shapely.geometry import Polygon, box

from pourbaix_r4.models import BoundaryRecord, CalculationInput, ResultSnapshot


def _clipped_vertices(
    vertices: Sequence[Sequence[float]], calculation_input: CalculationInput
) -> list[tuple[float, float]]:
    polygon = Polygon(vertices)
    if polygon.is_empty or not polygon.is_valid:
        return []
    ph_min, ph_max = calculation_input.ph_range
    potential_min, potential_max = calculation_input.potential_range
    clipped = polygon.intersection(box(ph_min, potential_min, ph_max, potential_max))
    if clipped.is_empty:
        return []
    polygons = [clipped] if clipped.geom_type == "Polygon" else list(getattr(clipped, "geoms", ()))
    coordinates: list[tuple[float, float]] = []
    for geometry in polygons:
        if geometry.geom_type != "Polygon":
            continue
        coordinates.extend((float(ph), float(potential)) for ph, potential in list(geometry.exterior.coords)[:-1])
    return coordinates


def calculate_snapshot(
    inputs: CalculationInput,
    entries: Sequence[object],
    *,
    diagram_factory: Callable[..., Any] = PourbaixDiagram,
    plotter_factory: Callable[[Any], Any] = PourbaixPlotter,
) -> ResultSnapshot:
    """Construct and clip a diagram exactly once for display and export consumers."""
    diagram = diagram_factory(entries, comp_dict=inputs.comp_dict)
    plotter = plotter_factory(diagram)
    stable_entries = tuple(diagram.stable_entries)
    labels = tuple(str(entry) for entry in stable_entries)
    boundaries: list[BoundaryRecord] = []
    for entry, label in zip(stable_entries, labels, strict=True):
        vertices = plotter.domain_vertices(entry)
        if vertices is None or len(vertices) < 3:
            continue
        for vertex_index, (ph, potential) in enumerate(_clipped_vertices(vertices, inputs)):
            boundaries.append(BoundaryRecord(label, ph, potential, vertex_index))
    return ResultSnapshot(
        calculation_input=inputs,
        stable_domain_labels=labels,
        boundaries=tuple(boundaries),
        entries_count=len(entries),
    )
