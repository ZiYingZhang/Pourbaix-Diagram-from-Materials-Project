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

    @property
    def comp_dict(self) -> dict[str, float]:
        return dict(self.closed_element_ratios)


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


@dataclass(frozen=True)
class BoundaryRecord:
    """One display-clipped vertex of an equilibrium domain boundary."""

    domain_label: str
    ph: float
    potential_v_she: float


@dataclass(frozen=True)
class ResultSnapshot:
    """The immutable source of truth for R4 plots, regions, and exports."""

    calculation_input: CalculationInput
    stable_domain_labels: tuple[str, ...]
    boundaries: tuple[BoundaryRecord, ...]
    entries_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
