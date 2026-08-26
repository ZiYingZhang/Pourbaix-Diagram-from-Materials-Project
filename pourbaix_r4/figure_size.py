"""Physical figure-size helpers shared by the UI, renderer, and exporters."""

from __future__ import annotations


_INCHES_PER_UNIT = {
    "inch": 1.0,
    "cm": 1.0 / 2.54,
    "mm": 1.0 / 25.4,
}


FIGURE_SIZE_PRESETS_CM: dict[str, tuple[float, float]] = {
    "Default": (18.0, 12.0),
    "Journal single column": (8.5, 6.0),
    "Journal double column": (18.0, 12.0),
    "Presentation 16:9": (33.8667, 19.05),
}


def convert_length(value: float, source_unit: str, target_unit: str) -> float:
    """Convert a physical length between centimetres, millimetres, and inches."""
    try:
        inches = float(value) * _INCHES_PER_UNIT[source_unit]
        return inches / _INCHES_PER_UNIT[target_unit]
    except KeyError as error:
        raise ValueError(f"Unsupported figure-size unit: {error.args[0]}") from error


def pixel_dimensions(width_inches: float, height_inches: float, dpi: float) -> tuple[int, int]:
    """Return the nearest whole-pixel export dimensions."""
    if width_inches <= 0 or height_inches <= 0 or dpi <= 0:
        raise ValueError("Figure dimensions and DPI must be greater than zero")
    return round(width_inches * dpi), round(height_inches * dpi)
