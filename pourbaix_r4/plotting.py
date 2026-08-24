"""Matplotlib rendering from immutable R4 result snapshots."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoMinorLocator

from pourbaix_r4.models import AppearanceSettings, InterestRegion, ResultSnapshot


class PlottingError(ValueError):
    """Raised for a display request incompatible with a result snapshot."""


def _domain_vertices(snapshot: ResultSnapshot) -> dict[str, list[tuple[float, float]]]:
    grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for boundary in snapshot.boundaries:
        grouped[boundary.domain_label].append((boundary.ph, boundary.potential_v_she))
    return dict(grouped)


def render_snapshot(
    snapshot: ResultSnapshot,
    appearance: AppearanceSettings,
    regions: Sequence[InterestRegion],
) -> Figure:
    """Render already-clipped snapshot geometry without fetching or recalculating."""
    figure = Figure()
    FigureCanvasAgg(figure)
    axis = figure.add_subplot(111)
    ph_min, ph_max = snapshot.calculation_input.ph_range
    potential_min, potential_max = snapshot.calculation_input.potential_range
    vertices_by_label = _domain_vertices(snapshot)
    known_labels = set(snapshot.stable_domain_labels)
    formal_plotter = snapshot.plotter_payload
    if formal_plotter is not None and hasattr(formal_plotter, "get_pourbaix_plot"):
        formal_plotter.get_pourbaix_plot(
            limits=(snapshot.calculation_input.ph_range, snapshot.calculation_input.potential_range),
            label_domains=appearance.show_ion_labels,
            label_fontsize=int(appearance.ion_label_font_size),
            ax=axis,
        )
    for region in regions:
        if region.label not in known_labels:
            raise PlottingError(f"Unknown interest region: {region.label}")
        vertices = vertices_by_label.get(region.label, [])
        if region.visible and len(vertices) >= 3:
            axis.add_patch(Polygon(vertices, closed=True, facecolor=region.color, alpha=region.opacity, edgecolor="none"))

    for label, vertices in vertices_by_label.items():
        if formal_plotter is not None and hasattr(formal_plotter, "get_pourbaix_plot"):
            continue
        if len(vertices) >= 2:
            closed_vertices = [*vertices, vertices[0]]
            xs, ys = zip(*closed_vertices, strict=True)
            axis.plot(xs, ys, color="black", linewidth=appearance.solid_line_width)
        if appearance.show_ion_labels and vertices:
            ph = sum(point[0] for point in vertices) / len(vertices)
            potential = sum(point[1] for point in vertices) / len(vertices)
            bbox = None
            if appearance.fill_ion_label_background:
                bbox = {
                    "facecolor": appearance.ion_label_background_color,
                    "alpha": appearance.ion_label_background_alpha,
                    "edgecolor": "none",
                }
            axis.text(ph, potential, label, fontname=appearance.ion_label_font, fontsize=appearance.ion_label_font_size, bbox=bbox)

    ph_values = (ph_min, ph_max)
    axis.plot(ph_values, tuple(-0.0591 * value for value in ph_values), color=appearance.hydrogen_line_color, linewidth=appearance.stability_line_width)
    axis.plot(ph_values, tuple(1.229 - 0.0591 * value for value in ph_values), color=appearance.oxygen_line_color, linewidth=appearance.stability_line_width)
    axis.set_xlim(ph_min, ph_max)
    axis.set_ylim(potential_min, potential_max)
    axis.set_xlabel(appearance.x_axis_label, fontsize=appearance.x_axis_label_size, fontname=appearance.axis_tick_font)
    axis.set_ylabel(appearance.y_axis_label, fontsize=appearance.y_axis_label_size, fontname=appearance.axis_tick_font)
    for spine in axis.spines.values():
        spine.set_linewidth(appearance.spine_width)
    axis.tick_params(which="major", direction=appearance.major_tick_direction, length=appearance.major_tick_length, width=appearance.major_tick_width, labelsize=appearance.axis_tick_font_size)
    if appearance.show_minor_ticks:
        axis.xaxis.set_minor_locator(AutoMinorLocator())
        axis.yaxis.set_minor_locator(AutoMinorLocator())
        axis.tick_params(which="minor", direction=appearance.major_tick_direction, length=appearance.minor_tick_length, width=appearance.minor_tick_width)
    return figure
