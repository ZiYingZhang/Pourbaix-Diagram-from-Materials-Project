"""Immutable value objects shared by the R4 application layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class CalculationInput:
    """Validated chemical system and electrochemical viewport."""

    elements: tuple[str, ...]
    closed_element_ratios: tuple[tuple[str, float], ...]
    ph_range: tuple[float, float]
    potential_range: tuple[float, float]
    ion_concentrations: tuple[tuple[str, float], ...] = ()
    filter_solids: bool = True

    @property
    def comp_dict(self) -> dict[str, float]:
        return dict(self.closed_element_ratios)

    @property
    def conc_dict(self) -> dict[str, float]:
        return dict(self.ion_concentrations)


@dataclass(frozen=True)
class InterestRegion:
    """Display-only styling for one calculated equilibrium domain."""

    label: str
    visible: bool = True
    color: str = "#B0C4DE"
    opacity: float = 0.4


@dataclass(frozen=True)
class AppearanceSettings:
    """Display preferences that must not alter a calculation snapshot."""

    show_ion_labels: bool = True
    ion_label_font: str = "Arial"
    ion_label_font_size: float = 22.0
    fill_ion_label_background: bool = False
    ion_label_background_color: str = "#FFFFFF"
    ion_label_background_alpha: float = 0.6
    axis_tick_font: str = "Arial"
    axis_tick_font_size: float = 24.0
    x_axis_label: str = "pH"
    x_axis_label_font: str = "Arial"
    x_axis_label_size: float = 28.0
    y_axis_label: str = "E (V vs. SHE)"
    y_axis_label_font: str = "Arial"
    y_axis_label_size: float = 28.0
    spine_width: float = 1.5
    solid_line_width: float = 2.0
    stability_line_width: float = 2.0
    major_tick_direction: str = "out"
    x_major_tick_interval: float | None = None
    y_major_tick_interval: float | None = None
    major_tick_length: float = 8.0
    major_tick_width: float = 1.0
    show_x_ticks: bool = True
    show_y_ticks: bool = True
    show_minor_ticks: bool = True
    minor_tick_length: float = 4.0
    minor_tick_width: float = 0.5
    show_x_tick_labels: bool = True
    show_y_tick_labels: bool = True
    hydrogen_line_color: str = "#FF0000"
    oxygen_line_color: str = "#0070C0"
    figure_width_inches: float = 18.0 / 2.54
    figure_height_inches: float = 12.0 / 2.54


@dataclass(frozen=True)
class BoundaryRecord:
    """One display-clipped vertex of an equilibrium domain boundary."""

    domain_label: str
    ph: float
    potential_v_she: float
    vertex_index: int = 0


@dataclass(frozen=True)
class ResultSnapshot:
    """The immutable source of truth for R4 plots, regions, and exports."""

    calculation_input: CalculationInput
    stable_domain_labels: tuple[str, ...]
    boundaries: tuple[BoundaryRecord, ...]
    entries_count: int
    plotter_payload: object | None = field(default=None, repr=False, compare=False)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
