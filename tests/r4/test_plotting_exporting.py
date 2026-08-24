from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Polygon

from pourbaix_r4.exporting import ExportError, export_boundaries, export_figure
from pourbaix_r4.models import AppearanceSettings, BoundaryRecord, CalculationInput, InterestRegion, ResultSnapshot
from pourbaix_r4.plotting import PlottingError, render_snapshot


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
            BoundaryRecord("Fe(s)", 7.0, 1.0),
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
    assert data["domain_label"].tolist() == ["Fe(s)", "Fe(s)", "Fe(s)"]


def test_export_boundaries_rejects_unknown_format_without_refetching(tmp_path):
    with pytest.raises(ExportError, match="Unsupported"):
        export_boundaries(_snapshot(), tmp_path / "boundaries.json", "json")


def test_render_snapshot_applies_r2_appearance_settings_and_interest_region_fill():
    appearance = AppearanceSettings(
        show_ion_labels=True,
        ion_label_font="DejaVu Sans",
        ion_label_font_size=15,
        x_axis_label="pH",
        y_axis_label="E (V vs. SHE)",
        spine_width=2.0,
        solid_line_width=1.5,
        stability_line_width=2.5,
        major_tick_direction="in",
        major_tick_length=7.0,
        major_tick_width=1.2,
        show_minor_ticks=True,
        minor_tick_length=3.0,
        minor_tick_width=0.7,
        hydrogen_line_color="#ff0000",
        oxygen_line_color="#0070c0",
    )
    figure = render_snapshot(
        _snapshot(), appearance, [InterestRegion("Fe(s)", color="#112233", opacity=0.3)]
    )
    axis = figure.axes[0]

    assert axis.get_xlim() == (0.0, 14.0)
    assert axis.get_ylim() == (-2.0, 4.0)
    assert axis.get_xlabel() == "pH"
    assert axis.get_ylabel() == "E (V vs. SHE)"
    assert axis.spines["left"].get_linewidth() == 2.0
    assert len(axis.patches) == 1
    assert axis.patches[0].get_alpha() == 0.3
    assert any(line.get_color() == "#ff0000" for line in axis.lines)
    assert any(line.get_color() == "#0070c0" for line in axis.lines)
    water_lines = [line for line in axis.lines if line.get_color() in {"#ff0000", "#0070c0"}]
    assert len(water_lines) == 2
    assert all(line.get_linestyle() == "--" for line in water_lines)


def test_render_snapshot_accepts_postprocessing_view_limits():
    figure = render_snapshot(
        _snapshot(),
        AppearanceSettings(),
        [],
        view_limits=((-1.0, 10.0), (-1.5, 2.5)),
    )

    assert figure.axes[0].get_xlim() == (-1.0, 10.0)
    assert figure.axes[0].get_ylim() == (-1.5, 2.5)


class SelfCrossingFormalPlotter:
    def get_pourbaix_plot(
        self,
        limits,
        label_domains,
        label_fontsize,
        show_water_lines,
        show_neutral_axes=True,
        ax=None,
    ):
        ax.plot([0.0, 14.0], [1.5, -1.0], color="black", linestyle="-")
        ax.plot([0.0, 14.0], [0.3, 1.8], color="black", linestyle="-")
        if show_neutral_axes:
            ax.plot([7.0, 7.0], [-4.0, 4.0], color="black", linestyle="-.")
            ax.plot([-2.0, 16.0], [0.0, 0.0], color="black", linestyle="-.")
        if label_domains:
            ax.text(7.0, 0.5, "Fe(s)", fontsize=label_fontsize)
        return ax


def test_render_snapshot_replaces_self_crossing_plotter_chords_with_snapshot_boundary():
    base = _snapshot()
    snapshot = ResultSnapshot(
        calculation_input=CalculationInput(
            elements=("Fe",),
            closed_element_ratios=(("Fe", 1.0),),
            ph_range=(-2.0, 16.0),
            potential_range=(-4.0, 4.0),
        ),
        stable_domain_labels=("Fe(s)",),
        boundaries=(
            BoundaryRecord("Fe(s)", -2.0, -1.0, 0),
            BoundaryRecord("Fe(s)", 16.0, -1.0, 1),
            BoundaryRecord("Fe(s)", 16.0, 2.0, 2),
            BoundaryRecord("Fe(s)", -2.0, 2.0, 3),
        ),
        entries_count=base.entries_count,
        plotter_payload=SelfCrossingFormalPlotter(),
    )

    figure = render_snapshot(snapshot, AppearanceSettings(), [])
    axis = figure.axes[0]
    black_solid_lines = [
        line for line in axis.lines
        if line.get_color() == "black" and line.get_linestyle() == "-"
    ]
    assert len(black_solid_lines) == 1
    line = black_solid_lines[0]
    boundary = Polygon(list(zip(line.get_xdata()[:-1], line.get_ydata()[:-1], strict=True)))
    assert boundary.is_valid
    assert not any(line.get_linestyle() == "-." for line in axis.lines)


def test_water_stability_lines_span_the_complete_active_view():
    figure = render_snapshot(
        _snapshot(),
        AppearanceSettings(),
        [],
        view_limits=((-2.0, 16.0), (-4.0, 4.0)),
    )

    water_lines = [
        line for line in figure.axes[0].lines
        if line.get_color() in {"#FF0000", "#0070C0"}
    ]
    assert len(water_lines) == 2
    assert all(tuple(line.get_xdata()) == (-2.0, 16.0) for line in water_lines)


def test_render_snapshot_rejects_unknown_interest_regions_without_substitution():
    with pytest.raises(PlottingError, match="Unknown interest region"):
        render_snapshot(_snapshot(), AppearanceSettings(), [InterestRegion("Unknown(s)")])


@pytest.mark.parametrize("image_format", ["png", "jpeg", "tiff", "svg"])
def test_export_figure_writes_supported_image_formats(tmp_path, image_format):
    figure = render_snapshot(_snapshot(), AppearanceSettings(), [])
    path = tmp_path / f"diagram.{image_format}"

    written = export_figure(figure, path, image_format, dpi=144, transparent=True)

    assert written == path
    assert path.stat().st_size > 0
    if image_format == "svg":
        assert "<svg" in path.read_text(encoding="utf-8")


def test_export_figure_rejects_unknown_format():
    figure = render_snapshot(_snapshot(), AppearanceSettings(), [])

    with pytest.raises(ExportError, match="Unsupported"):
        export_figure(figure, Path("unused.json"), "json", dpi=300, transparent=False)
